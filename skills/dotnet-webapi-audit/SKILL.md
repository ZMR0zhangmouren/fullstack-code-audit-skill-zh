---
name: dotnet-webapi-audit
description: ASP.NET Web API / REST API 框架专项审计工具。针对 API 鉴权、序列化、DTO 绑定、CORS、版本路由和错误返回进行白盒审计。
---

# ASP.NET Web API 框架专项审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 webapi 相关的入口定义、绑定转换、前置控制、敏感操作、安全配置抓手
- 若项目存在框架二次封装、统一扩展方法、平台基座或宿主包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（如已由 `dotnet-route-mapper` 生成，用于对齐 API 入口、绑定源与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（如需对齐匿名 API、P0/P1 分桶与授权边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（如需把 API 入口、序列化链和下游副作用链做交叉引用）

## 重点检查

- API 认证、匿名路由、版本路由、路由约束、OpenAPI 分组与网关/反向代理前缀映射
- System.Text.Json、Newtonsoft.Json TypeNameHandling、循环引用、ReferenceHandler、类型信息、多态序列化与错误输出中的敏感字段暴露
- DTO 绑定、FromBody/FromQuery/FromRoute/FromHeader、Patch/JsonPatchDocument、批量接口和 over-posting 风险
- CORS、Swagger、ProblemDetails、异常处理中间件、模型校验失败响应与调试信息暴露
- API key、HMAC、Cookie flags / JWT validation parameters、mTLS、自定义签名头与重放保护逻辑
- 文件上传、流式下载、回调/Webhook、后台管理 API 和内部 API 的边界是否清晰

## 枚举规则（强制细化）

- 枚举所有 ApiController、Minimal API、版本路由、RoutePrefix/MapGroup、自定义约束和网关前缀映射，记录外网可达路径与版本差异
- 优先搜索 ApiController、ProducesResponseType、FromBody、FromQuery、FromRoute、FromHeader、JsonPatchDocument、ProblemDetails、EnableCors、AddSwaggerGen、AddEndpointsApiExplorer
- 枚举输入 DTO、Patch 模型、批量接口、Webhook、回调地址、文件上传和流式下载入口，记录字段来源、批量写入能力与认证方式
- 枚举序列化配置：System.Text.Json、Newtonsoft.Json、ReferenceHandler、TypeNameHandling、自定义 JsonConverter、多态解析与错误格式化逻辑
- 对每个 API 记录：路由模板、认证方式、绑定源、序列化器、错误输出、文档暴露面、是否面向内部或外部调用
- **维度条（强制，2026-09-20）：签名重放**——签名中间件注册顺序与可达性（是否在鉴权/限流之后、是否可被全局短路或分支管道绕过）、签名入口路由暴露面、nonce/timestamp/replay cache 三件套在请求处理管线中的生效性逐项核对（请求处理面判定见本文件「机制扩展：签名请求重放保护」节；签名/验签实现面见 `dotnet-crypto-audit` 同名维度条，两文件互指、判定口径同一份）。不适用判定条件：目标无任何 API key + 签名/HMAC/Webhook 签名校验中间件或入口，且附 rg 否定证据（范围 + 模式，如 `rg "UseHmac|SignatureVerification|VerifySignature" {范围}` 零命中）方可标 `不适用`；否则禁裸「未覆盖」

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | API 接口暴露且版本/路由可达 | 存在外网可达的 API 端点（含版本路由/网关前缀），且匿名或弱认证可访问 | BLOCKED → 所有 API 均强认证且不可达，专项降为低优先级 |
| 二级 | 绑定/序列化存在绕过或敏感信息暴露 | DTO/Patch/批量接口存在 over-posting，或序列化配置（TypeNameHandling/ReferenceHandler）导致类型混淆/信息泄露 | BLOCKED → 绑定与序列化链完整无绕过，结论降级 |
| 三级 | 认证/授权链不完整导致越权 | API 认证方式缺失、JWT 验证参数宽松、CORS 配置过度开放，或内部 API 边界不清 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 API 入口 + 绑定/序列化配置 + 认证/授权链，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 API 路由 → 版本/网关前缀 → 认证方式 链路；
  2. 验证 DTO/Patch/批量接口的 over-posting 与序列化配置（TypeNameHandling/ReferenceHandler）风险；
  3. 评估 JWT/CORS/文档暴露面是否导致越权或信息泄露；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：API 外网可达 + 绑定/序列化绕过 + 认证/授权链不完整。输出 `确认漏洞`。
2. **待确认**：API/绑定/认证证据部分存在，但部署环境或运行时行为不可证实。输出 `待确认`。
3. **误报/无风险**：API 均强认证、绑定链完整、序列化配置安全、CORS 严格。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 ASP.NET Web API / Minimal API / 版本路由
  - 存在外网可达且匿名/弱认证的 API 端点
  - 或 DTO/Patch/批量接口存在 over-posting
  - 或序列化配置（TypeNameHandling/ReferenceHandler）不安全
- **测试用例建议**：
  - Happy Path：正常 API 请求经完整认证与绑定处理，返回正确响应
  - 边界/歧义：版本路由差异、JsonPatchDocument 字段覆盖、TypeNameHandling 类型混淆、Swagger 调试信息暴露
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（接口暴露确认）**：必须确认 API 路由、版本与中间件入口完整。
- 🔴 **CHECKPOINT B（参数与授权确认）**：必须确认绑定来源、校验与授权策略生效。
- 🔴 **CHECKPOINT C（响应与副作用确认）**：必须确认返回体与下游副作用路径可追溯。
- 🛑 **STOP**：若参数链与授权链未闭合，不得输出“低风险”结论。

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

## 输出要求

- 输出文件：framework_audit/webapi_{timestamp}.md
- 必须按 路由与版本、绑定与序列化、认证与跨域、错误返回与文档暴露 四个章节组织结果
- 每个问题点必须写明 受影响接口、输入绑定方式、认证上下文、响应类型、与漏洞专项的交叉点
- 必须单列 对外 API、内部 API、Webhook/回调 API 三类边界，避免将内外网假设混写

## 证据引用

- EVID_AUTH_TOKEN_DECODE_JUDGMENT
- EVID_AUTH_PATH_PROTECTED_MATCH
- EVID_DESER_OBJECT_TYPE_MAGIC_TRIGGER_CHAIN
- EVID_CFG_SECURITY_SWITCH_EVIDENCE

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 接口可达但认证方式不可确认 | 输出已知认证配置与入口证据 | 标记 `⚠️鉴权待验证`，禁止已确认越权 |
| DTO 绑定风险存在但字段映射不完整 | 输出绑定源与关键字段 | 结论降级为 PARTIAL |
| 序列化风险命中但运行配置不可见 | 记录默认配置与显式配置差异 | 降级为环境依赖，不给强结论 |
| CORS/文档暴露仅存在配置片段 | 标记暴露面并补充缺失项 | 仅给提示级风险，待联调确认 |

🔴 **STOP：认证链与绑定链未闭合时，不得输出“确认可利用”结论。**

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每个 skill 至少维护 2 个典型测试用例（happy path + 一条复杂场景），并在结果中标注用例 ID。
- 每轮评估至少 1 条用例执行 `full_test`；若受限只能 `dry_run`，必须记录 `dry_run_reason` 与补测计划。
- 通过标准至少同时满足：`意图达成`、`关键证据命中`、`输出格式合规`；任一不满足不得给出“通过”。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如“首先/其次/最后/综上/说白了/换句话说”）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出“确认可利用/可交付”。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

| # | 反模式 | 为什么不要做 | 正确做法 |
|---|---|---|---|
| 1 | 只凭 `[AllowAnonymous]` 就判越权漏洞 | 需结合资源操作与业务校验 | 结合权限检查与资源归属证据 |
| 2 | 忽略版本路由差异 | 不同版本安全策略可能不同 | 按版本分别记录结论 |
| 3 | 把 Swagger 暴露直接等同漏洞成立 | 暴露面≠可利用链闭合 | 区分信息暴露与实际利用链 |

输出类型映射：AUTH、DESER、CFG、LOGIC、CSRF。

## 机制扩展：签名请求重放保护（2026-09-14 台账轮）

### 机制描述与边界

不可信 signed request → freshness 校验缺失（nonce/timestamp/replay cache）→ 重放成功。攻击者捕获一次合法签名请求后原样或微调后再次提交，若服务端仅验签不校验新鲜性，重放请求被当作合法请求处理，造成重复扣款、重复下单等状态变更。

本 Skill（dotnet-webapi-audit）侧重**请求处理面**：签名中间件的注册顺序与可达性（是否在鉴权/限流之后、是否可被全局短路绕过）、签名入口路由的暴露面。签名与验签实现本身见 dotnet-crypto-audit 同名扩展，判定口径同一份。

台账边界（逐字）：签名有效 ≠ 请求新鲜；不与 HTTP 查询构造混并；签名算法或密钥管理问题不属本扩展。

### 重点检查与枚举抓手

每命中记录：文件、行号、中间件/路由、缺失的 freshness 组件。

- **签名验证入口**：API key + 签名的自定义中间件、`UseHmacSignature` / 自定义验签中间件、`SignatureVerification` 辅助方法的注册位置与作用范围。
- **freshness 三件套存在性**：
  - nonce 存储与唯一性校验：`IDistributedCache` / `MemoryCache` 中 nonce 记录的写入与查询，分布式部署下是否共享存储（单机 `MemoryCache` 在多实例下即失效）。
  - timestamp 窗口与偏移容忍：请求处理管线中 timestamp 偏差校验的存在性与偏移上限。
  - replay cache 过期策略：nonce/timestamp 记录的过期策略，过期前重复提交是否被拒。
- **签名覆盖范围**：被签名字符串是否包含 method、path、timestamp、nonce、body；路由重写/网关改写过 path 时签名是否失配。
- **中间件顺序与可达性**：验签中间件是否在端点执行前生效，是否存在更早的中间件短路（如全局异常处理吞掉验签失败）、MapGroup / 分支管道绕过验签。

### 验证矩阵

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **nonce 唯一性强制** | 确认请求处理管线中 nonce 用过即拒；多实例部署下 nonce 存储是否共享 | 用过即拒且跨实例共享 → ✅ 安全；单机缓存多实例或重复 nonce 可通过 → 🔴 高危待确认 |
| **timestamp 窗口校验** | 确认 timestamp 偏差校验在管线中生效且窗口外拒绝 | 窗口校验 fail-close → ✅ 安全；无窗口校验或容忍无限 → 🔴 高危待确认 |
| **replay cache 不可绕过** | 确认 cache miss（nonce 不存在）默认拒绝；确认无中间件短路或分支管道绕过验签 | miss 默认拒绝且不可绕过 → ✅ 安全；miss 默认放行或可绕过 → 🔴 高危待确认 |
| **签名覆盖完整性** | 核对 method+path+timestamp+nonce+body 全覆盖，含网关/代理改写 path 后的失配处理 | 全覆盖 → ✅ 安全；timestamp/nonce 不在签名内 → 🔴 高危待确认 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

### 判定规则

确认需同时闭合以下三个 EVID，缺一不可：

1. **freshness 缺失闭合**：签名验证入口缺少 nonce/timestamp/replay cache freshness 校验证据（`EVID_CRYPTO_REPLAY_FRESHNESS_ABSENT`）。
2. **重放实证闭合**：同一签名请求二次提交被接受的重放实证（`EVID_CRYPTO_REPLAY_ACCEPTANCE`）。
3. **影响闭合**：重放导致越权操作/状态变更的影响闭合证据（`EVID_CRYPTO_REPLAY_IMPACT_CONFIRM`）。

🔴 **确认阈值（台账原文）：必须证明 freshness 校验缺失且重放请求可被接受。** webapi 侧重请求处理面（中间件顺序、签名入口可达性），crypto 侧重签名/验签面，判定口径同一份。

### 测试建议

- **正向**：经真实管线捕获签名请求原样重放，确认被接受；篡改 timestamp 后经管线重放，确认仍通过。
- **负向**：nonce 唯一 + 窗口校验齐备时，重放请求在中间件层被拒。
- **回归**：新增签名端点或调整中间件顺序时，复核 freshness 三件套与验签中间件可达性。

### 证据引用

- `EVID_CRYPTO_REPLAY_FRESHNESS_ABSENT`：签名验证入口缺少 nonce/timestamp/replay cache freshness 校验证据
- `EVID_CRYPTO_REPLAY_ACCEPTANCE`：同一签名请求二次提交被接受的重放实证
- `EVID_CRYPTO_REPLAY_IMPACT_CONFIRM`：重放导致越权操作/状态变更的影响闭合证据
