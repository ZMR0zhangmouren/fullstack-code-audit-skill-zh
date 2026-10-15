---
name: node-csrf-audit
description: Node.js CSRF 审计工具。识别 express-session sameSite 配置、csurf（已废弃）后自建 token 校验、origin/referer 比对与状态变更端点的跨站提交风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js CSRF 审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与状态变更入口、token 生成与校验、origin/referer 比对、Cookie SameSite、豁免清单相关的共享抓手
- 若项目存在 CsrfMiddleware、FormGuard、MutationProtector、AdminActionGuard 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐状态变更入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、序列化配置、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- 状态变更端点（POST/PUT/PATCH/DELETE）无任何 CSRF 防护：无 token、无 origin 校验、无二次确认
- `csurf` 已于 2022 年被 npm 标记废弃，存量引用必须核查；自建 token 方案需验证生成-传输-校验闭环与豁免清单
- `express-session` 的 `cookie.sameSite` 未显式设置时依赖浏览器默认（Chrome 80+ 起为 Lax），Lax 不完全等同防护：老内核/Safari 行为不一致、GET 副作用入口、子域 Cookie 注入仍可绕过
- `sameSite: 'none'` 必须配合 `secure:true`，且跨站请求会携带 Cookie
- origin/referer 校验缺陷：`indexOf`/`startsWith` 子串匹配、允许空 origin、未比对协议与端口
- JSON POST + `application/json` content-type 限制的缓解意义（HTML 表单无法伪造该 content-type），需与 CORS 策略联动评估
- Next.js Server Actions 的内建防护（POST-only + Origin/Host 比对）；低版本或自定义 fetch/API Route 路径绕开内建防护的场景
- NestJS Guard、GraphQL Mutation、multipart 上传等非 HTML 表单提交面的覆盖；改密/转账类敏感操作缺少二次确认

## 枚举规则（强制细化）

- 枚举所有状态变更路由：`app.post(`、`app.put(`、`app.patch(`、`app.delete(`、`router.post(`、`@Post(`、`@Put(`、`@Mutation(`、Server Actions（`"use server"`）
- 优先搜索 `csurf`、`csrf(`、`csrfToken`、`_csrf`、`csrf-csrf`、`doubleSubmit`、`req.headers.origin`、`req.headers.referer`、`Sec-Fetch-Site`、`sameSite`、`cookie.sameSite`
- 对每个状态变更入口记录：认证方式（Cookie/session）、token 生成与校验位置、中间件挂载范围与豁免清单、content-type 分支、是否跨站可触达
- 枚举 `express-session`/`cookie-session` 初始化配置与 `res.cookie(...)` 显式 `sameSite` 参数的实际下发值
- 枚举敏感操作（改密、转账、绑定邮箱/手机）是否存在独立第二因子且服务端复核
- 若存在二次封装，必须逐层展开到真实路由处理函数

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| CSRF token 校验 | 自建 token（csrf-csrf 双提交 cookie）、全局中间件 | 检查中间件是否覆盖全部状态变更路由、生成-传输-校验闭环、豁免清单内容 | 全覆盖且 fail-close（无 token 拒绝）→ ✅ 安全；豁免清单含状态变更或仅部分路由挂载 → 🔴 高危；挂载顺序在鉴权后无法确认 → ⚠️ 待验证 |
| origin/referer 校验 | `req.headers.origin`/`req.headers.referer` 与 Host 白名单比对 | 核对是否严格全等、空 origin 是否拒绝、是否存在子串匹配 | 严格全等且拒绝空 origin → ✅ 安全；`indexOf`/`startsWith` 子串匹配或允许空值 → ⚠️ 可绕过 |
| SameSite Cookie | `express-session` 的 `cookie.sameSite`、`res.cookie` 显式参数 | 读取会话中间件配置与实际 Set-Cookie 下发值 | `strict` → ✅ 安全；`lax` 显式设置 → ⚠️（GET 副作用/子域注入仍可绕过）；`none` 或未设置依赖浏览器默认 → 🔴 高危 |
| content-type 限制 | `express.json()` 仅接受 `application/json` | 确认端点是否仅 JSON 可达且无 form/multipart 兼容分支，CORS 是否未放开 | 仅 JSON 且 CORS 严格 → ✅ 缓解；接受 form/urlencoded/multipart → 🔴 高危 |
| 二次确认 | 改密/转账/绑定操作需重输密码或验证码 | 检查敏感操作是否有服务端复核的第二因子 | 有服务端复核 → ✅ 安全；仅前端确认 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：跨站可携带凭据的状态变更入口疑似缺失全部 CSRF 防护
- `待确认`：上下文显示可疑模式（如仅 SameSite=Lax），但 token 校验、origin 比对或中间件覆盖范围不清晰
- `误报`：防护已验证为 fail-close（token 全覆盖 / origin 严格全等），或入口为只读 GET

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到跨站可携带凭据且无有效防护的状态变更入口证据 → `确认漏洞`
- 找到 token 全覆盖 / origin 严格校验的 fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_CSRF_STATE_CHANGE_ENDPOINT` + `EVID_NODE_CSRF_TOKEN_CHECK`（校验缺失或存在绕过分支），且无 origin/referer 校验、无二次确认
- Cookie 会话 `sameSite:'none'` 或未设置（`EVID_NODE_CSRF_COOKIE_SAMESITE`），同时 token 校验缺失或可绕过
- origin 校验为子串匹配 / 允许空 origin 的 fail-open 实现，攻击页可携带跨站请求通过校验

### ⚠️待验证

- token 中间件存在，但挂载范围 / 中间件顺序（`EVID_NODE_CFG_MIDDLEWARE_ORDER`）无法确认是否覆盖全部状态变更路由
- 显式 `SameSite=Lax`，但存在 GET 副作用入口或子域 Cookie 注入场景需补证
- Next.js Server Actions 内建防护依赖 `next` 版本，当前版本与自定义 fetch 调用路径无法确认

### 误报

- 纯 GET 只读端点，无状态变更副作用
- token 校验全路由覆盖且 fail-close（`EVID_NODE_CSRF_TOKEN_CHECK` + `EVID_NODE_CSRF_COOKIE_SAMESITE` 双证据闭合），无可绕过分支
- 端点仅接受 `application/json` 且 origin 严格校验、CORS 未放开；敏感操作另有服务端复核（`EVID_NODE_CSRF_SECOND_CONFIRM` 佐证）

## 测试建议（强制）

### 正向测试

- 构造跨站自动提交表单 / `fetch` no-cors 请求：携带 Cookie 触发无防护的状态变更端点
- 验证 `sameSite:'none'` 会话下跨站 POST 可成功执行副作用
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 无 token / 错误 token / 过期 token 请求被拒绝（fail-close）
- 伪造 `Origin: https://evil.com` 与空 origin 请求被 origin 校验拒绝
- 验证 content-type 限制下 `text/plain` / form 提交无法到达业务逻辑

### 回归测试

- 修复后复测，确认 token 中间件仍覆盖全部状态变更路由
- 复测新增路由未遗漏防护，豁免清单未扩大
- 验证 SameSite / origin 白名单变更后仍保持 fail-close

## 证据引用

- `EVID_NODE_CSRF_STATE_CHANGE_ENDPOINT`
- `EVID_NODE_CSRF_TOKEN_CHECK`
- `EVID_NODE_CSRF_COOKIE_SAMESITE`
- `EVID_NODE_CSRF_SECOND_CONFIRM`
- 可选叠加：`EVID_NODE_SESS_COOKIE_FLAGS`（Cookie 全量 flags）、`EVID_NODE_CFG_MIDDLEWARE_ORDER`（CSRF 中间件挂载顺序）

## 输出

- `node/vuln_audit/csrf_{timestamp}.md`
- `node/vuln_poc/csrf_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
