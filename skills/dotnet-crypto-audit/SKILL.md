---
name: dotnet-crypto-audit
description: .NET 加密与密钥安全审计工具。识别弱算法、硬编码密钥、不安全模式、随机数与签名校验缺陷。
---

# .NET 加密与密钥安全审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与算法选择、密钥生成、密钥存储、DataProtection、证书和令牌签名相关的共享抓手
- 若项目存在 CryptoHelper、KeyStore、TokenSigner、PasswordHasherWrapper 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于关联登录、签名、加解密调用入口与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（用于关联认证、票据与权限边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（可作为算法/密钥缺陷影响到具体入口的交叉证据，不是前置硬依赖）

重点检查：

- MD5、SHA1、DES、3DES、RC2、ECB、CBC 固定 IV、弱 PBKDF 参数、不安全 HMAC 和自定义加密封装
- Random、Guid、时间戳、可预测 nonce、RNGCryptoServiceProvider / RandomNumberGenerator 的使用边界与替换错误
- 密钥、IV、salt、pepper、JWT signing key、DataProtection key、加密证书、API secret 的来源、轮换和存储位置
- ASP.NET Core DataProtection、DPAPI、Azure Key Vault、证书存储、HSM、User Secrets 与环境变量中的密钥管理模式
- 加密结果是否缺少完整性校验、AEAD、重放保护、版本号、上下文绑定或租户隔离
- 密码哈希、令牌签名、文件加密、cookie 保护、remember-me token 和 magic link 生成逻辑
- 日志、异常、调试输出、配置快照和前端返回中是否泄露敏感密钥材料

## 重点检查

- 弱哈希算法：MD5、SHA1 用于密码存储或完整性校验
- 弱加密算法：DES、3DES、RC2、RC4、ECB 模式
- 密钥管理：硬编码密钥、appsettings 明文密钥、代码中的 Base64 编码密钥
- IV/Salt 问题：固定 IV、空 Salt、Salt 长度不足、IV 重用
- 随机数：使用 System.Random 而非 RandomNumberGenerator 生成安全相关值
- 密码哈希：未使用 bcrypt/scrypt/Argon2/PBKDF2 或迭代次数不足
- 签名校验：JWT 算法混淆（none/HS256 vs RS256）、Webhook 签名未验证
- DataProtection：密钥轮换策略、跨应用共享密钥、持久化位置安全性

## 证据引用

- EVID_CRYPTO_ALGO_SELECTION
- EVID_CRYPTO_KEY_SOURCE
- EVID_CRYPTO_MODE_PADDING_RANDOMNESS

## 枚举规则（强制细化）

- 枚举所有 HashAlgorithm、Aes、RSA、ECDsa、ProtectedData、DataProtection、JwtSecurityTokenHandler、自定义 CryptoHelper 的使用点
- 优先搜索 MD5、SHA1、ECB、CBC、IV、salt、key、secret、signing、encrypt、decrypt、Protect、Unprotect 等关键字
- 枚举密码哈希、票据签名、文件加密、字段加密、魔术链接、remember-me token、API 签名、Webhook 签名场景
- 对每个加密点记录：算法、模式、随机性来源、密钥来源、轮换策略、输出使用场景和完整性保护情况
- **维度条（强制，2026-09-20）：签名重放**——签名/验签入口的 nonce 唯一性约束、timestamp 窗口校验、replay cache 三件套逐项核对（签名/验签面判定口径见本文件「机制扩展：签名请求重放保护」节；请求处理面——中间件顺序与签名入口可达性见 `dotnet-webapi-audit` 同名维度条，两文件互指、判定口径同一份）。不适用判定条件：目标无任何签名/验签/HMAC/Webhook 签名校验入口，且附 rg 否定证据（范围 + 模式，如 `rg "HMACSHA256|VerifyData|SignData|SignatureVerification" {范围}` 零命中）方可标 `不适用`；否则禁裸「未覆盖」

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 加密/哈希操作存在 | HashAlgorithm/Aes/RSA/ProtectedData/DataProtection 等存在且被实际用于安全敏感数据 | BLOCKED → 无加密/哈希操作，专项结束 |
| 二级 | 弱算法/不安全模式被使用 | MD5/SHA1/DES/3DES/ECB/固定 IV/System.Random 等被用于密码/签名/加密 | BLOCKED → 算法与模式安全，结论降级 |
| 三级 | 密钥管理缺陷可导致实际利用 | 硬编码密钥、appsettings 明文密钥、无轮换策略、密钥泄露到日志/异常/前端 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中加密/哈希操作 + 算法/模式配置 + 密钥管理，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 安全敏感数据 → 加密/哈希调用 → 算法/模式 → 密钥来源 链路；
  2. 验证 MD5/SHA1/DES/ECB/固定 IV/System.Random 等弱算法/模式的使用场景；
  3. 评估密钥/IV/salt 来源（硬编码/配置/密钥库）、轮换策略与泄露面（日志/异常/前端）；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：加密/哈希操作存在 + 弱算法/不安全模式 + 密钥管理缺陷可导致利用。输出 `确认漏洞`。
2. **待确认**：加密/哈希操作存在但算法安全性或密钥来源证据不足。输出 `待确认`。
3. **误报/无风险**：使用安全算法（AES-GCM/SHA-256/Argon2）、RandomNumberGenerator、密钥存储于 KeyVault/HSM、有轮换策略且无泄露。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在加密/哈希/签名操作（HashAlgorithm/Aes/RSA/ProtectedData/DataProtection）
  - 使用弱算法（MD5/SHA1/DES/ECB）或不安全模式（固定 IV/System.Random）
  - 或密钥硬编码/明文存储/无轮换/泄露到日志
- **测试用例建议**：
  - Happy Path：正常加密/哈希/签名操作使用安全算法与密钥管理
  - 边界/歧义：JWT 算法混淆（none/HS256 vs RS256）、DataProtection 跨应用共享密钥、硬编码密钥搜索、日志中密钥泄露
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用

证据引用：

- EVID_CRYPTO_ALGO_SELECTION
- EVID_CRYPTO_KEY_SOURCE
- EVID_CRYPTO_MODE_PADDING_RANDOMNESS

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（算法确认）**：必须确认算法/模式/填充与业务用途的对应关系。
- 🔴 **CHECKPOINT B（密钥来源确认）**：必须给出 key/iv/salt 的来源与轮换证据。
- 🔴 **CHECKPOINT C（完整性确认）**：必须确认是否存在签名/AEAD/重放防护。
- 🛑 **STOP**：若密钥来源或完整性证据缺失，禁止输出“已确认可利用”高强度结论。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 仅发现弱算法名，无法确认实际调用场景 | 补齐算法到业务数据流的调用证据 | 降级为待验证，不输出可利用强结论 |
| 密钥/IV/salt 来源不清 | 追踪到配置/密钥库/运行时注入来源 | 标记轮换与来源缺口，保守评估风险 |
| 完整性保护链无法验证（签名/AEAD） | 补齐加密与验签双向证据链 | 仅输出环境依赖或待验证结论 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认可利用”。**

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每次产出前至少执行 2 条典型测试用例（happy path + 边界/歧义场景各 1 条），并记录预期与实际差异。
- 默认要求 `full_test >= 1`；若只能 `dry_run`，必须在结论中标记 `confidence=LOW`，并给出补测计划与负责人。
- 通过标准：关键字段齐全、证据链可回溯、结论级别与门禁状态一致；任一失败则禁止标记“已通过/可交付”。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如“首先/其次/最后/综上/说白了/换句话说”）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出“确认可利用/可交付”。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

- 反模式：仅凭算法名推断全局可利用。正确做法：结合调用场景、密钥来源与数据流判断。
- 反模式：把 Base64/配置项当“安全存储”。正确做法：区分编码与密钥管理。
- 反模式：忽略完整性保护（AEAD/签名）。正确做法：同时审查机密性与完整性。
- 反模式：缺失轮换证据却判“风险可控”。正确做法：降级并标注轮换缺口。

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如“可能有风险/建议关注/视情况而定/大概率”等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

最小输出片段（可直接复用）：

```md
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```

## 输出

- vuln_audit/crypto_{timestamp}.md
- 可选：vuln_poc/crypto_{timestamp}.md（如能构造复现请求、弱配置验证步骤或环境依赖验证链）

## 机制扩展：签名请求重放保护（2026-09-14 台账轮）

### 机制描述与边界

不可信 signed request → freshness 校验缺失（nonce/timestamp/replay cache）→ 重放成功。攻击者捕获一次合法签名请求后原样或微调后再次提交，若服务端仅验签不校验新鲜性，重放请求被当作合法请求处理，造成重复扣款、重复下单等状态变更。

本 Skill（dotnet-crypto-audit）侧重**签名/验签面**：签名与验签实现、`HMACSHA256` / `RSA` 验签入口、被签名材料（timestamp/nonce/body）的覆盖范围。请求处理与中间件顺序问题见 dotnet-webapi-audit 同名扩展，判定口径同一份。

台账边界（逐字）：签名有效 ≠ 请求新鲜；不与 HTTP 查询构造混并；签名算法或密钥管理问题不属本扩展。

### 重点检查与枚举抓手

每命中记录：文件、行号、验签/校验点、缺失的 freshness 组件。

- **签名验证入口**：`HMACSHA256` / `RSA` / `ECDsa` 验签调用点、`SignatureVerification` 辅助方法、API key + 签名的自定义中间件、Webhook 签名校验。
- **freshness 三件套存在性**：
  - nonce 存储与唯一性校验：`IDistributedCache` / `MemoryCache` 中是否存在 nonce 记录，验签后是否写入，二次提交是否命中已存记录。
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

1. **freshness 缺失闭合**：签名验证入口缺少 nonce/timestamp/replay cache freshness 校验证据（`EVID_CRYPTO_REPLAY_FRESHNESS_ABSENT`）。
2. **重放实证闭合**：同一签名请求二次提交被接受的重放实证（`EVID_CRYPTO_REPLAY_ACCEPTANCE`）。
3. **影响闭合**：重放导致越权操作/状态变更的影响闭合证据（`EVID_CRYPTO_REPLAY_IMPACT_CONFIRM`）。

🔴 **确认阈值（台账原文）：必须证明 freshness 校验缺失且重放请求可被接受。** 签名算法或密钥管理问题不属本扩展，另行归口。

### 测试建议

- **正向**：捕获一次合法签名请求原样重发，确认被接受；篡改 timestamp 或 nonce 后重放，确认仍可通过。
- **负向**：nonce 唯一性 + timestamp 窗口校验齐备时，重放请求被拒。
- **回归**：新增签名端点（含 Webhook、回调、开放 API）时，复核 freshness 三件套。

### 证据引用

- `EVID_CRYPTO_REPLAY_FRESHNESS_ABSENT`：签名验证入口缺少 nonce/timestamp/replay cache freshness 校验证据
- `EVID_CRYPTO_REPLAY_ACCEPTANCE`：同一签名请求二次提交被接受的重放实证
- `EVID_CRYPTO_REPLAY_IMPACT_CONFIRM`：重放导致越权操作/状态变更的影响闭合证据
