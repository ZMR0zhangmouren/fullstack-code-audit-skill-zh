---
name: node-crypto-audit
description: Node.js 加密与密钥审计工具。识别 md5/sha1 安全场景滥用、createCipheriv 弱参数、Math.random 生成 token、单次 sha256 口令哈希与 JWT secret 弱配置风险，输出分级、证据和修复建议。
---

# Node.js 加密与密钥审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与算法选择、随机数来源、密钥生成与存储、口令哈希相关的共享抓手
- 若项目存在 cryptoUtil、hashService、tokenHelper、passwordHasher 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐登录、签名、加解密入口与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **静态证据驱动**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致
- 职责边界：JWT/Cookie 会话配置（alg 钉死、过期、注销）归 `node-session-cookie-audit`，本专项管算法原语、随机源与密钥材料

## 重点检查

- md5 / sha1 用于签名、完整性校验、口令存储等安全场景
- `createCipheriv` 弱参数：`des`、`des3`、`aes-*-ecb`、固定 iv、空 salt
- `Math.random` 生成 token、验证码、重置链接（应 `crypto.randomBytes` / `getRandomValues`）
- 口令单次 `sha256` / `md5` 存储（应 bcrypt / scrypt / argon2 / pbkdf2 慢哈希）
- JWT secret 弱口令字面量、入仓、硬编码默认值
- 硬编码 key / iv / salt、Base64 字面量当密钥、无盐哈希
- Webhook / 支付回调签名未校验，或 HMAC 比较用 `==` 而非 `crypto.timingSafeEqual`

## 枚举规则（强制细化）

- rg 搜索：`createHash(`、`createCipheriv(`、`createDecipheriv(`、`createHmac(`、`randomBytes(`、`Math.random(`、`pbkdf2`、`scrypt`、`bcrypt`、`argon2`、`jwt.sign(`、`secret`、`md5`、`sha1`、`des-`、`ecb`
- 对每个加密点记录：算法、模式、iv/salt 来源、密钥来源（环境/密钥服务/字面量）、随机数来源、输出用途（口令哈希/签名/完整性/加密）
- 区分安全场景与非安全场景：md5/sha1 用于缓存键、ETag 不计风险；用于口令、票据、校验值计风险
- 枚举口令哈希、签名、加密、验证码、重置链接等场景的完整调用链
- 若存在二次封装，必须逐层展开到真实 `crypto` / 第三方库调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 口令哈希方案 | bcrypt / scrypt / argon2 / pbkdf2 | 确认口令存储使用的哈希函数与 cost/迭代参数 | 自适应慢哈希且参数达标 → ✅ 安全；单次 md5/sha256 → 🔴 高危 |
| 随机数来源 | `crypto.randomBytes` / `getRandomValues` | 核对 token、验证码、重置链接的随机源 | CSPRNG 且长度充足 → ✅ 安全；`Math.random` / 时间戳 → 🔴 高危 |
| 算法与模式 | `createCipheriv` 参数串 | 核对算法标识、mode、iv 来源与唯一性 | AES-GCM/CBC + 随机 iv → ✅ 安全；des/ecb/固定 iv → 🔴 高危 |
| 密钥来源 | 环境注入 / 密钥管理服务 / 字面量 | 追踪 secret、key 声明位置与默认回退 | 注入且无弱默认 → ✅ 安全；硬编码或入仓 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：弱算法、弱随机或弱密钥疑似用于口令、token、加解密等安全敏感场景
- `待确认`：上下文显示可疑模式，但外部输入来源、barrier 行为或调用链不清晰
- `误报`：输入来自固定常量 / 枚举映射，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到外部可控输入进入 Sink 位的证据 → `确认漏洞`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_CRYPTO_WEAK_ALGO` + `EVID_NODE_CRYPTO_HASH_MODE`：口令经单次 md5/sha256 存储且无慢哈希
- `EVID_NODE_CRYPTO_RANDOM_SOURCE`：`Math.random` 生成会话 token、验证码或密码重置链接
- `EVID_NODE_CRYPTO_WEAK_ALGO` + `EVID_NODE_CRYPTO_KEY_SOURCE`：des/ecb 或固定 iv 加密且密钥硬编码、入仓
- `EVID_NODE_CRYPTO_KEY_SOURCE`：JWT secret 为弱口令字面量且无环境注入覆盖

### ⚠️待验证

- `createHash('sha1')` 命中但业务用途（缓存键 vs 完整性校验）不清晰
- 加密调用存在，但 iv/key 来源需补调用链才能确认
- 口令哈希经二次封装，未展开到 bcrypt/argon2 真实调用

### 误报

- token 全部由 `crypto.randomBytes(32)` 生成，口令使用 bcrypt 且 cost >= 10
- md5/sha1 仅用于 ETag、缓存键等非安全场景，无安全语义
- 密钥由环境或密钥管理服务注入且有轮换记录，算法为 AES-GCM

## 测试建议（强制）

### 正向测试

- 用已知口令碰撞 md5/sha256 库验证口令可还原；多次采样 `Math.random` 验证 token 可预测
- 用弱密钥解密密文验证 `createCipheriv` 弱参数可利用
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- bcrypt/scrypt 口令无法彩虹表还原；`crypto.randomBytes` token 无法通过历史序列预测
- 环境注入密钥缺失时服务拒绝启动（fail-close）

### 回归测试

- 修复后复测算法与随机源未回退；复测密钥来源切换后无新增字面量
- 新增加密点默认接入 CSPRNG 与慢哈希规范

## 证据引用

- `EVID_NODE_CRYPTO_WEAK_ALGO`
- `EVID_NODE_CRYPTO_KEY_SOURCE`
- `EVID_NODE_CRYPTO_RANDOM_SOURCE`
- `EVID_NODE_CRYPTO_HASH_MODE`

## 输出

- `node/vuln_audit/crypto_{timestamp}.md`
- `node/vuln_poc/crypto_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）

## 机制扩展：签名请求重放保护（2026-09-14 台账轮）

### 机制描述与边界

不可信 signed request → freshness 校验缺失（nonce/timestamp/replay cache）→ 重放成功。攻击者捕获一次合法签名请求后原样或微调后再次提交，若服务端仅验签不校验新鲜性，重放请求被当作合法请求处理，造成重复扣款、重复下单等状态变更。

本 Skill（node-crypto-audit）侧重**签名/验签面**：`crypto.createHmac` / `crypto.createVerify` 验签实现、API key + signature 路由的验签入口、被签名材料（timestamp/nonce/body）的覆盖范围。请求处理与中间件顺序问题归 node-webapi-audit 同名扩展（待扩展，node-webapi-audit 尚未挂接本轮机制扩展；兑现前以本章节签名/验签面口径为准），判定口径同一份。

台账边界（逐字）：签名有效 ≠ 请求新鲜；不与 HTTP 查询构造混并；签名算法或密钥管理问题不属本扩展。

### 重点检查与枚举抓手

每命中记录：文件、行号、验签/校验点、缺失的 freshness 组件。

- **签名验证入口**：`crypto.createHmac('sha256', key).update(...).digest()` 验签调用点、express/fastify 签名中间件、API key + signature 路由、Webhook 签名校验。
- **freshness 三件套存在性**：
  - nonce 存储与唯一性校验：内存 Map / Redis replay cache 中是否存在 nonce 记录，验签后是否写入，二次提交是否命中已存记录。
  - timestamp 窗口与偏移容忍：是否校验 timestamp 与服务器时间的偏差上限，容忍窗口是否可配置且合理。
  - replay cache 过期策略：nonce/timestamp 记录是否有过期时间，过期前是否强制拒绝重复。
- **签名覆盖范围**：被签名字符串是否包含 method、path、timestamp、nonce、body；仅签名 body 或仅签名 path 时，timestamp/nonce 可篡改而不破坏签名。

### 验证矩阵

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **nonce 唯一性强制** | 确认验签通过后 nonce 写入存储，且后续请求携带相同 nonce 时被拒绝 | 用过即拒 → ✅ 安全；重复 nonce 可通过或 nonce 不存储 → 🔴 高危待确认 |
| **timestamp 窗口校验** | 确认 timestamp 偏差校验存在，含时钟偏移容忍上限，窗口外请求被拒 | 窗口校验 fail-close → ✅ 安全；无窗口校验或容忍无限 → 🔴 高危待确认 |
| **replay cache 不可绕过** | 确认 cache miss（nonce 不存在）时默认拒绝而非默认放行；cache 故障时的行为 | miss 默认拒绝 → ✅ 安全；miss 默认放行或故障 fail-open → 🔴 高危待确认 |
| **签名覆盖完整性** | 核对待签名字符串构造，确认 method+path+timestamp+nonce+body 全覆盖 | 全覆盖且任一缺失导致验签失败 → ✅ 安全；timestamp/nonce 不在签名内 → 🔴 高危待确认 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

### 判定规则

确认需同时闭合以下三个 EVID，缺一不可：

1. **freshness 缺失闭合**：签名验证入口缺少 nonce/timestamp/replay cache freshness 校验证据（`EVID_NODE_CRYPTO_REPLAY_FRESHNESS_ABSENT`）。
2. **重放实证闭合**：同一签名请求二次提交被接受的重放实证（`EVID_NODE_CRYPTO_REPLAY_ACCEPTANCE`）。
3. **影响闭合**：重放导致越权操作/状态变更的影响闭合证据（`EVID_NODE_CRYPTO_REPLAY_IMPACT_CONFIRM`）。

🔴 **确认阈值（台账原文）：必须证明 freshness 校验缺失且重放请求可被接受。** 签名算法或密钥管理问题不属本扩展，另行归口。

### 测试建议

- **正向**：捕获一次合法签名请求原样重发，确认被接受；篡改 timestamp 或 nonce 后重放，确认仍可通过。
- **负向**：nonce 唯一性 + timestamp 窗口校验齐备时，重放请求被拒。
- **回归**：新增签名端点（含 Webhook、回调、开放 API）时，复核 freshness 三件套。

### 证据引用

- `EVID_NODE_CRYPTO_REPLAY_FRESHNESS_ABSENT`：签名验证入口缺少 nonce/timestamp/replay cache freshness 校验证据
- `EVID_NODE_CRYPTO_REPLAY_ACCEPTANCE`：同一签名请求二次提交被接受的重放实证
- `EVID_NODE_CRYPTO_REPLAY_IMPACT_CONFIRM`：重放导致越权操作/状态变更的影响闭合证据
