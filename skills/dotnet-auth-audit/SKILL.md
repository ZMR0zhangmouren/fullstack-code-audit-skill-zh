---
name: dotnet-auth-audit
description: .NET 认证与授权审计工具。识别 ASP.NET Core Identity、Cookie、JWT、Policy、Role、Claim 与资源归属校验，输出鉴权映射与 AUTH 风险分析。
---

# .NET Auth Audit

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与认证方案、授权策略、声明映射、匿名例外、外部登录和会话态相关的共享抓手
- 若项目存在 AuthService、PermissionChecker、PolicyResolver、TokenHelper 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 模式

- STATIC_MAPPING：只生成 auth_mapping 与 P0/P1 分桶
- TRACE_AUDIT：在 trace 存在时输出完整 AUTH 风险分析

## 输入依赖

- 必需：`source_path`
- `STATIC_MAPPING` 模式可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（如已由 `dotnet-route-mapper` 生成，用于统一入口、参数来源与 `route_id`）
- `TRACE_AUDIT` 模式必需：`route_tracer/{route_id}/trace_{timestamp}.md`
- `TRACE_AUDIT` 模式可选：`route_tracer/{route_id}/trace_summary_{timestamp}.md`
- 如通过 `dotnet-audit-pipeline` 执行，`TRACE_AUDIT` 模式中的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致
- 可选：`design_intent/design_intent_{timestamp}.md`（意图层参考：设计中的权限矩阵、角色与租户边界声明，用于补全枚举与判定基准，禁止作为 EVID 引用源，见 `shared/AUDIT_EXECUTION_COMMON.md` §9）

## 重点检查

- [Authorize]、AllowAnonymous、Policy、Role、Claim、AuthenticationSchemes 与全局过滤器之间的优先级和覆盖关系
- JWT、Cookie、Session、Identity、Windows/Auth、OpenID Connect、API Key、自定义签名票据的解析与校验流程
- TokenValidationParameters、签名算法、密钥轮换、issuer/audience/clock skew、ticket persistence 与滑动过期配置
- 资源归属校验、租户隔离、organizationId/tenantId/userId 与 route/body 参数之间的一致性，识别 IDOR 和越权
- Controller、Minimal API、Hub、GraphQL Resolver、Background API、WCF Service 等不同入口的自定义鉴权链和遗漏点
- 外部身份源映射、本地角色缓存、claim 转换、 impersonation、sudo/admin switch 和后门角色逻辑
- 登录、登出、密码重置、二次验证、remember me、设备信任和异常回退分支是否产生绕过面

## 枚举规则（强制细化）

- 若 `design_intent` 产物存在，优先核对其「权限与租户边界意图」与实际授权定义的差异（差异登记为文档-实现漂移，不直接升级为漏洞结论）
- 枚举所有 [Authorize]、AllowAnonymous、Policy、Roles、AuthenticationSchemes、RequireAuthorization、MapGroup 级授权定义
- 优先搜索 AddAuthentication、AddAuthorization、TokenValidationParameters、CookieAuthenticationOptions、IdentityOptions、IAuthorizationHandler
- 枚举 Controller、Minimal API、Hub、GraphQL Resolver、WCF Service、后台管理 API 和内部 API 的认证授权入口
- 枚举登录、登出、注册、密码重置、2FA、外部登录、设备信任、租户切换、管理员代登等身份流转接口
- 对每个授权点记录：入口类型、认证方案、权限判断来源、资源归属字段、异常/回退分支、默认允许路径
- **维度条（强制，2026-09-20）：错误响应一致性**——登录、找回密码、注册、2FA 等认证端点的错误响应一致性逐端点核对：状态码、错误文案、时序可区分信号三类差异面均须给出结论（枚举面、验证矩阵与判定阈值见本文件「机制扩展：账号枚举」节）。不适用判定条件：目标无任何认证/注册/找回端点，且附 rg 否定证据（范围 + 模式，如 `rg "SignIn|PasswordSignIn|FindByEmail" {范围}` 零命中）方可标 `不适用`；否则禁裸「未覆盖」

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **认证方案执行** | 确认 `[Authorize]`/`RequireAuthorization` 标注后，认证中间件是否真实执行（非仅标注） | 真实执行且失败时拒绝 → ✅ 安全；标注存在但中间件未注册/被跳过 → 🔴 高危 |
| **授权策略解析** | 读取 Policy/Role/Claim 校验源码，确认是否为 fail-close（无匹配策略 → 拒绝） | fail-close（无匹配拒绝） → ✅ 安全；fail-open（无匹配默认允许） → ⚠️ 可绕过；无策略校验 → 🔴 高危 |
| **资源归属校验（IDOR）** | 确认资源操作前是否校验当前用户/租户对目标资源的归属权 | 有严格的资源归属校验 → ✅ 安全；仅有身份校验无资源归属 → ⚠️ 待确认；无校验 → 🔴 高危 |
| **匿名例外与回退分支** | 逐入口核对 `AllowAnonymous` 覆盖面，确认回退分支（如认证失败后的默认行为）是否默认允许 | 无意外匿名入口，回退分支拒绝 → ✅ 安全；存在未记录的匿名入口或回退分支允许 → 🔴 高危 |
| **Token 校验完整性** | 确认 JWT/Token 校验是否完整：签名验证、issuer、audience、过期时间、clock skew | 全部校验且密钥安全 → ✅ 安全；跳过签名验证或仅解析不校验 → 🔴 高危；部分校验 → ⚠️ 待确认 |
| **权限提升与特权切换** | 确认是否存在 impersonation、sudo/admin switch、后门角色等特权切换逻辑 | 无特权切换或有严格的二次校验 → ✅ 安全；存在可被利用的特权切换路径 → 🔴 高危 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

## 二阶段判定（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

1. **阶段一（临时结论）**：对每条命中先标记 `确认漏洞候选` / `待确认` / `误报`
2. **阶段二（强制追证）**：
   - 若阶段一为 `确认漏洞候选` → 必须完成 Barrier 验证矩阵全部相关项，通过后才能标记 `已确认`
   - 若阶段一为 `待确认` → 必须向下追至少一跳调用链或下游解析器，直到可判定为止
   - 若阶段二仍无法闭合 → 保持 `待确认`，并明确记录缺失哪一跳证据

## 判定规则（强制细化）

### 确认漏洞

至少满足以下任一条件：

1. 认证中间件未注册或被跳过，`[Authorize]` 标注仅存在但未真实执行
2. 授权策略为 `fail-open`（无匹配策略默认允许），或资源归属校验缺失导致 IDOR
3. `AllowAnonymous` 覆盖范围过大，或存在未记录的匿名入口可绕过认证
4. JWT/Token 校验跳过签名验证，或仅解析 claims 不验证合法性
5. 存在可被利用的特权切换路径（如普通用户可通过参数切换为 admin 角色）
6. 嵌套/递归结构（如多层 PolicyResolver 封装）中顶层存在校验，但子层未执行同级校验

### 待确认

1. 上下文显示可疑模式（如 `[Authorize]` 标注），但认证中间件注册与执行顺序无法确认
2. Barrier 函数（如资源归属校验）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路（如消息队列触发后台任务）中的权限上下文传递未闭合
4. Token 校验参数（如 `TokenValidationParameters`）配置分散在多处，无法确认完整校验行为

### 误报

1. 入口有明确的 `AllowAnonymous` 且业务设计如此（如公开 API），非漏洞
2. 递归所有层级均复用同一 fail-close 授权策略校验器
3. 资源归属校验严格且不可绕过，当前用户仅能访问自己拥有的资源
4. Token 校验完整（签名+issuer+audience+过期），密钥管理安全

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造越权请求（如修改 `userId` 参数访问他人资源、删除 Token 签名部分、切换 role 参数），验证漏洞确实存在
- **负向测试**：构造被 barrier 拦截的输入（如无效 Token、无权限角色的 JWT、跨租户资源 ID），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径（如回退分支默认允许、新匿名入口）

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 证据引用（TRACE_AUDIT）

- EVID_AUTH_PATH_PROTECTED_MATCH
- EVID_AUTH_TOKEN_DECODE_JUDGMENT
- EVID_AUTH_PERMISSION_CHECK_EXEC
- EVID_AUTH_IDOR_OWNERSHIP_CONDITION

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（入口与方案确认）**：必须确认入口的认证方案与授权元数据。
- 🔴 **CHECKPOINT B（权限链确认）**：必须确认权限检查执行点与资源归属条件。
- 🔴 **CHECKPOINT C（异常分支确认）**：必须确认匿名例外/回退分支是否可绕过。
- 🛑 **STOP**：若权限链未闭合，结论降级为 `⚠️待验证`，禁止强结论。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 仅发现授权标注，未定位真实权限执行点 | 追踪到策略解析与资源归属校验代码 | 降级 `⚠️待验证`，保留待补证越权项 |
| 匿名例外与回退分支证据不完整 | 逐入口核对 `AllowAnonymous` 与默认策略 | 暂不输出绕过确认，仅给验证路径 |
| 认证通过但授权链无法证明 | 补齐 claim/role/policy 到资源操作的映射 | 禁止强结论，维持保守风险描述 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认越权”。**

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

- 反模式：只看 `[Authorize]` 标注就判安全。正确做法：验证策略、资源归属与运行时分支是否真正执行。
- 反模式：把“仅认证”误判为“已授权”。正确做法：区分认证通过与权限校验通过。
- 反模式：忽略 `AllowAnonymous`/回退分支。正确做法：逐入口核对匿名例外覆盖面。
- 反模式：证据不足时输出越权确认。正确做法：降级 `⚠️待验证` 并列出缺失证据点。

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如“可能有风险/建议关注/视情况而定/大概率”等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

最小输出片段（可直接复用）：

```md
- 命中ID：M{hash}（文件路径片段+行号+序号，用于跨阶段追踪和回归对齐）
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- test_id：T{hash}（关联测试用例）
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```

## 输出

- STATIC_MAPPING：auth_audit/auth_mapping_{timestamp}.md
- TRACE_AUDIT：auth_audit/auth_audit_report_{timestamp}.md

## 机制扩展：账号枚举（2026-09-14 台账轮）

### 机制描述与边界

不可信登录请求 → 认证错误响应 → 账号存在性/认证状态/错误类型可区分信号。攻击者通过对比成功、失败、账号不存在三种路径在状态码、响应体、时序上的差异，推断账号是否存在、是否锁定、认证方式等状态。

台账边界（逐字）：纳入既有认证审计错误响应一致性维度，不新建枚举 Skill；不属于本扩展：认证绕过/口令爆破（归既有认证维度）。

### 重点检查与枚举抓手

至少覆盖以下四类枚举面，每命中记录：文件、行号、端点、差异信号类型（状态码/响应体/时序）：

- **登录端点错误响应分支**：ASP.NET Identity `SignInManager.CheckPasswordSignInAsync` / `PasswordSignInAsync` 结果分支是否按 `Succeeded` / `IsLockedOut` / `IsNotAllowed` / `RequiresTwoFactor` 返回不同响应；`ChallengeResult` / `ForbidResult` / `BadRequest` 的差异是否泄露账号状态。
- **找回密码流程响应差异**：`UserManager.FindByEmailAsync` 返回 null 与发送重置邮件两条路径的响应是否一致；「该邮箱未注册」类提示是否直接暴露存在性。
- **注册流程存在性提示**：用户名/邮箱唯一性校验是否返回「该用户名已被占用」等可区分提示，且提示颗粒度是否到具体字段值。
- **响应统一化中间件缺失**：是否无 `StatusCodePages` / 统一错误过滤器，或自定义异常过滤器在不同分支返回不同结构，导致差异泄漏；时序上账号不存在是否短路返回（少一次哈希校验）形成可观测时间差。

### 验证矩阵

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **响应一致性统一** | 分别提交 正确口令+存在账号 / 错误口令+存在账号 / 任意口令+不存在账号，比对三次响应的状态码与响应体指纹 | 三路径指纹完全一致 → ✅ 安全；任一可区分 → 🔴 高危待确认 |
| **时序均衡** | 对存在与不存在账号各测响应耗时分布，确认不存在账号是否走同代价路径（哈希校验不短路） | 恒定时序或统一代价 → ✅ 安全；不存在账号明显更快 → ⚠️ 待确认 |
| **错误信息泛化** | 检查错误消息与错误码是否区分「用户不存在」/「密码错误」/「账号锁定」 | 统一为泛化文案（如「用户名或密码错误」）且无状态码区分 → ✅ 安全；文案或码值可区分 → 🔴 高危待确认 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

### 判定规则

确认需同时闭合以下三个 EVID，缺一不可：

1. **端点面闭合**：登录/找回/注册枚举面证据（`EVID_AUTH_ENUM_ENDPOINT_SURFACE`）。
2. **可观察差异闭合**：成功/失败/不存在账号间可观察差异（状态码/响应体/时序至少一项）证据（`EVID_AUTH_ENUM_OBSERVABLE_DIFF`）。
3. **影响闭合**：账号存在性或认证状态可被推断的影响闭合证据（`EVID_AUTH_ENUM_IMPACT_CONFIRM`）。

🔴 **确认阈值（台账原文）：仅理论差异不得确认——必须证明可观察差异（响应体/状态码/时序至少一项）。**

已统一响应且时序均衡为误报。

### 测试建议

- **正向**：以不存在账号与错误口令各发一次登录请求，确认响应差异（状态码/响应体/时序至少一项）可观察。
- **负向**：统一响应 + 时序均衡后，两路径不可区分。
- **回归**：新增认证端点（含找回密码、注册、2FA 校验）时，对响应一致性做复核。

### 证据引用

- `EVID_AUTH_ENUM_ENDPOINT_SURFACE`：登录/找回/注册端点枚举面证据
- `EVID_AUTH_ENUM_OBSERVABLE_DIFF`：成功/失败/不存在账号间可观察差异（状态码/响应体/时序至少一项）证据
- `EVID_AUTH_ENUM_IMPACT_CONFIRM`：账号存在性或认证状态可被推断的影响闭合证据
