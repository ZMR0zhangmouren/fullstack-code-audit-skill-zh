---
name: dotnet-minimal-api-audit
description: ASP.NET Core Minimal API 框架专项审计工具。针对端点注册、路由组、参数绑定、端点过滤器、结果过滤和 lambda 处理器进行白盒审计。
---

# ASP.NET Core Minimal API 框架专项审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 Minimal API 相关的入口定义、绑定转换、前置控制、敏感操作抓手
- Minimal API 特性包括：MapGet/MapPost/MapPut/MapDelete/MapPatch、MapGroup/RouteGroupBuilder、EndpointFilter/IEndpointFilter、Results/IResult、请求参数绑定 lambda、结果过滤
- 若项目存在框架二次封装、统一扩展方法、Rext 的 MapGroup 封装、平台基座或宿主包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（如已由 `dotnet-route-mapper` 生成，用于对齐 Minimal API 入口、参数绑定与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（如需对齐匿名端点、P0/P1 分桶、授权元数据或资源归属边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（如需将端点过滤器、结果过滤和下游副作用链做交叉引用）

## 重点检查

- **路由与端点注册**：MapGet/MapPost/MapPut/MapDelete/MapPatch、MapGroup/RouteGroupBuilder、WithTags/WithName/WithOpenApi、路由模板、HTTP 方法约束、前缀继承行为
- **参数绑定**：[FromQuery]、[FromRoute]、[FromBody]、[FromForm]、[FromHeader]、自动绑定规则、BindAsync、TryParse、IParsable<T>、Records 作为 DTO
- **Lambda 处理器**：内联 lambda vs 静态方法 vs 本地函数闭包捕获、变量作用域、安全敏感操作的闭包逃逸
- **端点过滤器**：IEndpointFilter 实现、EndpointFilterContext、EndpointFilterInvocationBehavior、过滤器注册与执行顺序、授权与异常过滤器
- **结果过滤**：Results 工厂方法、Results.Extensions、IResult 实现、流式响应 vs 完整响应、内容协商
- **认证与元数据**：.RequireAuthorization()、匿名端点、元数据传播、路由组继承、WithMetadata、IAuthorizeData
- **OpenAPI 集成**：AddOpenApi、OpenApiRequestBody/Response、SwaggerGen 集成、XML 注释暴露
- **文件与流处理**：IFormFile 绑定、Stream 返回、File(Permission) 和 PhysicalFile 使用、PathTraversaldanger
- **最简化 API 独有风险**：无 Controller 类的全局过滤器盲区、无 ActionFilter 的参数校验缺失、无 [ValidateAntiForgeryToken] 的 CSRF 窗口、Startup.Configure 中的显式注册缺失

## 枚举规则（强制细化）

- **端点注册枚举**：
  - 搜索关键字：MapGet、MapPost、MapPut、MapDelete、MapPatch、MapGroup、RouteGroupBuilder、WithTags、WithName、WithOpenApi、RequireAuthorization、DisableAutoAcceptAuthorization
  - 记录：路由模板、HTTP 方法、组前缀、端点过滤器、认证要求、元数据类型
  - 识别路由组前缀继承行为、WithGroupName vs MapGroup 前缀差异

- **参数绑定枚举**：
  - 搜索关键字：[FromQuery]、[FromRoute]、[FromBody]、[FromForm]、[FromHeader]、BindAsync、TryParse、IParsable<T>、ParsableEndpointFilter
  - 记录：绑定源、参数名、默认值、可空性、Records 类型、复杂对象展开字段
  - 识别隐式绑定 vs 显式绑定差异、绑定失败时的默认行为

- **Lambda 处理器枚举**：
  - 搜索关键字：app.MapGet.*lambda、delegate、Func<HttpContext, ...>、Func<...Request, ...Response>、async (ctx =>
  - 记录：lambda 捕获的变量、闭包中的服务注入、静态成员 vs 实例成员、安全敏感操作的闭包来源
  - 识别内联 lambda 处理器中的 request/response 数据流

- **端点过滤器枚举**：
  - 搜索关键字：IEndpointFilter、EndpointFilterContext、EndpointFilterDelegate、AddEndpointFilter、EndpointFilterInvocationBehavior
  - 记录：过滤器类型（同步/异步）、注册位置、执行顺序（PipelineOrderFilter）、参数读取、返回值修改、异常处理
  - 识别授权过滤器、元数据过滤器、日志过滤器的交叉点

- **结果过滤枚举**：
  - 搜索关键字：Results.Ok、Results.NotFound、Results.Extensions、IResult、ExecuteAsync、IStatusCodeHttpWriter
  - 记录：结果类型、状态码、内容协商、流式响应 vs 完整响应、Results.Extensions 自定义实现
  - 识别 Results<T> 泛型包装、隐式转换、ProblemDetails 集成

- **元数据与认证枚举**：
  - 搜索关键字：WithMetadata、IAuthorizeData、AuthorizeAttribute、AllowAnonymousAttribute、EndpointMetadataCollection
  - 记录：授权策略名称、角色/声明要求、匿名例外、端点优先级
  - 识别路由组继承的元数据覆盖规则

- **OpenAPI 枚举**：
  - 搜索关键字：AddOpenApi、OpenApiRequestBody、OpenApiResponse、AddSwaggerGen、AddEndpointsApiExplorer、IncludeXmlComments
  - 记录：请求体类型、响应类型、XML 注释暴露、标签分组、版本差异
  - 识别 OpenAPI 文档中的敏感字段暴露

- **文件处理枚举**：
  - 搜索关键字：IFormFile、IFormFileCollection、File(Permission)、PhysicalFile、Path.Combine、ExtractToDirectory、archive
  - 记录：文件保存路径、扩展名校验、MIME 类型、内容Disposition、落盘点
  - 识别路径穿越风险、zip 炸弹、文件名注入

- 对每个端点记录：路由模板、HTTP 方法、参数绑定方式、处理器类型（lambda/方法）、过滤器链、认证元数据、返回类型、OpenAPI 可见性、与漏洞专项的交叉点

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | Minimal API 端点存在且可达 | MapGet/MapPost/MapPut/MapDelete/MapPatch 存在且外网可达 | BLOCKED → 无可达 Minimal API 端点，专项降为低优先级 |
| 二级 | 参数绑定/过滤器存在绕过 | 隐式绑定导致 over-posting、EndpointFilter 执行顺序错误、或 lambda 闭包捕获敏感数据 | BLOCKED → 绑定与过滤器链完整无绕过，结论降级 |
| 三级 | 认证缺失/元数据传播导致可利用 | RequireAuthorization 缺失、路由组元数据继承错误、匿名端点暴露敏感操作 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 Minimal API 端点 + 参数绑定/过滤器 + 认证/元数据，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 Map* 端点 → 路由组继承 → 参数绑定 → EndpointFilter 链路；
  2. 验证隐式绑定 over-posting、EndpointFilter 顺序、lambda 闭包敏感数据捕获；
  3. 评估 RequireAuthorization/AllowAnonymous 与路由组元数据继承的正确性；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：端点可达 + 参数绑定/过滤器绕过 + 认证缺失/元数据传播错误。输出 `确认漏洞`。
2. **待确认**：端点/绑定/认证证据部分存在，但过滤器执行顺序或元数据继承不可证实。输出 `待确认`。
3. **误报/无风险**：端点不可达或已保护，绑定显式且校验完整，EndpointFilter 顺序正确，认证元数据无继承错误。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 Minimal API 端点（MapGet/MapPost/MapPut/MapDelete/MapPatch）
  - 端点外网可达且匿名或弱认证可访问
  - 或隐式参数绑定导致 over-posting
  - 或 EndpointFilter 执行顺序错误、lambda 闭包捕获敏感数据
- **测试用例建议**：
  - Happy Path：正常 Minimal API 请求经完整绑定与过滤器处理，认证正确
  - 边界/歧义：MapGroup 元数据继承覆盖、隐式绑定字段注入、lambda 闭包变量逃逸、IFormFile 路径穿越、CSRF 窗口（无 Antiforgery）
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用

## 证据引用

- EVID_AUTH_PATH_PROTECTED_MATCH
- EVID_AUTH_PERMISSION_CHECK_EXEC
- EVID_DESER_OBJECT_TYPE_MAGIC_TRIGGER_CHAIN
- EVID_CFG_SECURITY_SWITCH_EVIDENCE
- EVID_FILE_RESOLVED_TARGET
- EVID_FILE_PATH_NORMALIZATION
- EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT
- EVID_SSRF_URL_NORMALIZATION
- EVID_XSS_OUTPUT_POINT
- EVID_CSRF_STATE_CHANGE_HANDLER_EXEC

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（端点确认）**：必须先确认 Map* 端点、路由组继承元数据与认证要求。
- 🔴 **CHECKPOINT B（绑定与过滤确认）**：必须确认参数绑定链和 EndpointFilter 执行链。
- 🔴 **CHECKPOINT C（副作用确认）**：必须说明 lambda/handler 是否触发敏感下游操作。
- 🛑 **STOP**：若端点元数据与执行链未闭合，结论降级为 `⚠️待验证/环境依赖`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| Map* 端点清单与元数据不完整 | 补齐路由组继承、授权与过滤器链 | 降级 `⚠️待验证/环境依赖` |
| 参数绑定来源不明确 | 分析显式/隐式绑定与失败默认行为 | 暂不输出强结论，仅给验证路径 |
| handler 副作用链未闭合 | 追踪到敏感下游调用与响应路径 | 保守描述风险并保留待补证 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认安全”。**

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

- 反模式：只枚举 Map* 不追踪过滤器链。正确做法：补齐 EndpointFilter 与授权元数据执行顺序。
- 反模式：忽略隐式参数绑定。正确做法：明确绑定源与失败默认行为。
- 反模式：把匿名端点与内部端点混写。正确做法：按边界分组并分别评估。
- 反模式：执行链未闭合就下强结论。正确做法：降级 `⚠️待验证/环境依赖`。

输出类型映射：AUTH、DESER、CFG、LOGIC、CSRF、FILE、SQL、SSRF、XSS。

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

- 输出文件：framework_audit/minimal_api_{timestamp}.md
- 必须按 端点注册与路由组、参数绑定与 Lambda 处理器、端点过滤器与结果过滤、认证与元数据传播、OpenAPI 暴露、文件与流处理 六个章节组织结果
- 每个问题点必须写明 受影响端点、绑定方式、处理器类型（lambda/方法）、过滤器链、认证上下文、响应类型、与漏洞专项的交叉点
- 必须单列 匿名端点、内部端点、文件处理端点、Webhook/回调端点 四类边界，避免将内外网假设混写
- 必须列出 Minimal API 独有风险：全局过滤器盲区、参数校验缺失、CSRF 窗口、显式注册缺失
- 若发现 lambda 处理器中的闭包安全敏感操作，必须在 项目内抓手 章节记录闭包变量来源