---
name: node-session-cookie-audit
description: Node.js 会话与 Cookie 审计工具。识别 JWT 算法混淆、弱/硬编码密钥、Cookie flags 缺失、会话生命周期缺陷等风险，输出分级、证据与修复建议。
---

# Node.js 会话与 Cookie 审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 JWT 签名/验证、Cookie 设置、Session 配置、会话生命周期相关的共享抓手
- 若项目存在 AuthService、TokenManager、SessionStore 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、序列化配置、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **静态证据驱动**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `jwt.verify` 未钉死算法，存在 RS256→HS256 混淆或 `alg:none` 绕过风险
- JWT 弱/硬编码密钥，或密钥长度不足
- JWT 过期校验缺失（`expiresIn` / `maxAge` 未配置）
- Cookie 三属性（`HttpOnly` / `Secure` / `SameSite`）缺失或配置错误
- `express-session` 使用默认名、弱 secret 或未启用安全 Cookie
- `cookie-session` 弱签名密钥或未启用 `signed`
- 注销不彻底：`req.session.destroy()` 未调用或客户端 Cookie 未清除

## 枚举规则（强制细化）

- 枚举所有 `jwt.sign`、`jwt.verify`、`jsonwebtoken`、`jose`、`express-session`、`cookie-session`、`res.cookie(`、`sameSite`、`httpOnly`、`secure:`、`algorithms:` 调用点与配置对象
- 对每个 JWT 调用点记录：算法选项、密钥来源、过期时间、`aud`/`iss`/`sub` 校验、是否允许 `none` 算法
- 对每个 Session/Cookie 配置点记录：Cookie flags、`secret`/`keys` 来源、session name、过期策略、注销处理
- 检查 `jwt.verify` 是否显式传入 `algorithms` 数组并钉死算法
- 检查 `jwt.sign` 是否显式指定 `algorithm` 并避免 `none`
- 检查密钥是否来自环境变量/KMS/Vault，而非硬编码字符串或短密钥
- 检查 `res.cookie` 是否同时设置 `httpOnly`、`secure`、`sameSite`
- 检查 `express-session` 的 `secret` 长度与来源、`name` 是否自定义、`cookie.secure` / `cookie.httpOnly` / `cookie.sameSite` 是否启用
- 检查 `cookie-session` 的 `keys` 是否强随机且 `signed` 为 `true`
- 检查登录成功后是否重新生成 session ID（会话固定防护）
- 检查注销路由是否调用 `req.session.destroy()` 并清除客户端 Cookie
- 若存在二次封装，必须逐层展开到真实 JWT / Session / Cookie 调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| algorithms 数组钉死 | `jwt.verify(token, secret, { algorithms: ['HS256'] })` | 检查 verify/sign 是否显式指定算法并拒绝 `none` | 算法白名单且禁用 none → ✅ 安全；未传 `algorithms` 或允许 `none` → 🔴 高危 |
| 密钥来自安全存储 | 密钥来自 `process.env.JWT_SECRET` / KMS / Vault；长度足够（HS256≥256 bits） | 检查密钥在源码中是否硬编码、是否可被逆向 | 来自安全存储且长度足够 → ✅ 安全；硬编码 / 短密钥 / 默认 secret → 🔴 高危 |
| Cookie 三属性齐全 | `res.cookie(name, value, { httpOnly: true, secure: true, sameSite: 'strict' })` | 检查所有 Cookie 设置点是否同时配置 HttpOnly、Secure、SameSite | 三属性均正确配置 → ✅ 安全；任一缺失 → ⚠️ 待确认；全缺失 → 🔴 高危 |
| 会话轮换/注销失效 | 登录后 `req.session.regenerate()`；注销 `req.session.destroy()` + 清除 Cookie | 检查登录/注销生命周期处理 | 登录轮换且注销彻底 → ✅ 安全；不轮换或注销不彻底 → ⚠️ 待确认 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：JWT/Session/Cookie 配置存在明显缺陷且可被利用
- `待确认`：上下文显示可疑模式，但配置来源、运行时值或调用链不清晰
- `误报`：配置符合安全基线，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到配置缺陷可被利用的证据 → `确认漏洞`
- 找到固定安全配置 / fail-close 证据 → `误报`
- 仍缺少关键调用链或运行时配置 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知/非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG` 配合 `EVID_NODE_SESS_JWT_ALG_PINNED`、`EVID_NODE_SESS_SECRET_SOURCE`、`EVID_NODE_SESS_COOKIE_FLAGS` 或 `EVID_NODE_SESS_LIFECYCLE` 中任意一项，且缺陷可被利用
- `jwt.verify` 未传入 `algorithms`，或允许 `none`，导致 RS256→HS256 混淆
- JWT 密钥为硬编码短字符串或公开可获取
- Cookie 未设置 `HttpOnly` / `Secure` / `SameSite`，导致 XSS 窃取 / CSRF 携带
- `express-session` 使用默认 `name`、弱 `secret`、未启用安全 Cookie 选项
- 注销未调用 `req.session.destroy()`，服务端会话仍有效

### ⚠️待验证

- 配置项（如 `secret`）引用环境变量，但无法确认运行时实际值是否足够强
- 生产/开发分支条件影响 Cookie `secure` 设置，静态无法确认部署环境
- 存在封装层，无法确认底层 JWT 库实际接收的 options

### 误报

- `jwt.verify` 显式钉死 `algorithms` 并拒绝 `none`
- 密钥来自安全存储且长度符合算法要求
- 所有 Cookie 均正确设置 `HttpOnly` / `Secure` / `SameSite`
- 登录后重新生成 session ID，注销彻底销毁会话并清除客户端 Cookie

## 测试建议（强制）

### 正向测试

- 构造 RS256→HS256 算法混淆攻击：使用公钥作为 HMAC 密钥签名 token 并提交
- 构造 `alg:none` JWT 并验证是否被服务端接受
- 构造过期 / 无效签名 token 验证拒绝逻辑
- 验证 XSS 场景下未设置 `HttpOnly` 的 Cookie 可被脚本读取
- 验证跨站请求未设置 `SameSite` 的 Cookie 是否被携带
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 提交正确签名的 token，验证正常通过
- 提交算法混淆 / `alg:none` / 过期 token，验证被拒绝
- 验证 `Secure` Cookie 在 HTTPS 环境下正常传输、HTTP 环境下不被发送

### 回归测试

- 修复后复测，确认 `algorithms` 已钉死且 `none` 被拒绝
- 复测密钥轮换流程，确认未重新引入硬编码密钥
- 验证 Cookie flags 与 session 生命周期在新增路由中保持一致

## 证据引用

- `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG`
- `EVID_NODE_SESS_JWT_ALG_PINNED`
- `EVID_NODE_SESS_SECRET_SOURCE`
- `EVID_NODE_SESS_COOKIE_FLAGS`
- `EVID_NODE_SESS_LIFECYCLE`

## 输出

- `node/vuln_audit/session-cookie_{timestamp}.md`
- `node/vuln_poc/session-cookie_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
