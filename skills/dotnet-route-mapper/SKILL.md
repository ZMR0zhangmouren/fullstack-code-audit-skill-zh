---
name: dotnet-route-mapper
description: .NET Web 入口与参数映射分析工具。从 ASP.NET Core、MVC、Web API、Minimal API、SignalR、GraphQL、WCF 源码中提取完整入口、参数结构与请求模板。
---

# .NET Route & Endpoint Mapper

## 目标

分析 .NET Web 项目源码，提取**完整**的 HTTP 路由入口与请求参数结构，生成可用于安全测试的请求模板（Burp/Repeater 风格），并自动保存为 Markdown。

## CRITICAL：完整输出（强制）

此 Skill 必须输出所有发现的入口与接口，不允许省略：

- 禁止出现省略占位符；必须输出完整的路由、参数和请求模板
- 禁止只输出“关键接口”或“高危接口”
- 每条入口必须包含：入口类型、HTTP 方法或操作名、路径规则、处理器位置、参数结构、完整请求模板或调用模板
- 对 Controller 场景，必须把 Controller 级与 Action 级路由、版本、Area、绑定来源和返回类型差异完整展开

## 核心输入

用户提供：

- `source_path`：.NET 项目、解决方案或仓库根目录

可选：

- `context_path`：若存在反向代理、网关前缀、PathBase、服务前缀，可用于拼接完整外部路径，但必须有配置或代码证据来源
- `codegraph_index_status_{timestamp}.md`：若存在 `codegraph/` 目录下的索引状态文件，可优先通过 CodeGraph 工具加速 Controller/Action 枚举与路由识别

（唯一真源：本节为准；与 pipeline 输入参数透传差异见 IO_PATH_CONVENTION.md）

## 输出目录结构（建议）

```text
{output_path}/
├── route_mapping/
│   ├── routes_{timestamp}.md
│   ├── params_{timestamp}.md
│   └── controller_inventory_{timestamp}.md
└── quality/
     └── route_mapper_validation_{timestamp}.md
```

路径与流水线合并模式下的对应关系见 shared/IO_PATH_CONVENTION.md。
统一的 route mapping 产物格式模板见 shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md。

## CodeGraph 加速分支（可选）

若 `codegraph/codegraph_index_status_{timestamp}.md` 存在且 `codegraph_status = AVAILABLE`：

1. 优先通过 `codegraph explore "ASP.NET controllers and routes in {source_path}"` 获取 Controller/Action/路由映射
2. 通过 `codegraph query --kind method` 补充 action 方法列表与签名
3. 通过 `codegraph node {controller_symbol}` 读取 Controller 源码与 Attribute 路由声明
4. 将 CodeGraph 返回的路由符号与手动静态分析结果交叉验证：
   - 一致项：直接采用，减少重复 Read/Grep
   - 差异项：标记 `⚠️需人工复核`，以手动分析为准
   - CodeGraph 独有项（如 Source Generator 生成的路由）：记录来源并纳入输出
5. CodeGraph 无法识别的场景（如动态路由、Convention-based 路由在 `Program.cs` 中注册）：仍走手动分析

若 `codegraph_status != AVAILABLE` 或索引状态文件不存在：完全回退现有静态分析流程，不报错、不阻塞。

**约束**：CodeGraph 加速不改变 routes/params 的输出格式与字段要求；仅改变信息获取方式。

## 覆盖范围（必做）

1. ASP.NET Core / MVC / Web API 的 Controller 路由（必做）
	- [Route]、[HttpGet]、[HttpPost]、[HttpPut]、[HttpDelete]、[HttpPatch]、[HttpHead]、[HttpOptions]
	- [AcceptVerbs] 多方法路由
	- Controller 级 [Route] 与 Action 级 [Route]/[Http*] 的组合
	- Conventional Routing：MapControllerRoute、MapDefaultControllerRoute、Area 路由、legacy 路由模板
	- Attribute Routing 与 Conventional Routing 并存时的匹配优先级与最终路径组合
	- API Versioning：URL segment、query、header、media type 版本传递方式
	- Area：AreaAttribute、MapAreaControllerRoute、模块前缀与管理后台路由
	- ControllerBase 与 Controller 的差异：View/页面型 Controller 与纯 API Controller 必须区分
2. ASP.NET Core Minimal API
	- MapGet/MapPost/MapPut/MapDelete/MapPatch/MapMethods
	- MapGroup、MapFallback、RouteGroupBuilder 前缀与 Filter
3. SignalR Hub
	- Hub Method、OnConnectedAsync/OnDisconnectedAsync 引发的服务端入口
4. GraphQL
	- Query / Mutation / Subscription 的公开入口与操作名
5. WCF
	- ServiceContract / OperationContract

## Controller 场景枚举规则（强制细化）

对每个 Controller / Action，必须显式识别以下信息：

1. 路由声明来源
	- Controller 级特性
	- Action 级特性
	- Program.cs / Startup.cs 中的 conventional route
	- Area / versioning / gateway prefix / PathBase
2. 最终路径拼接规则
	- Controller 模板 + Action 模板 + Area + 版本前缀 + 路由约束
3. HTTP 方法
	- 来自 [HttpGet]/[HttpPost]/[AcceptVerbs] 等显式声明
	- 若为 conventional route 且未显式限制，需要标注方法限制不确定或由 action 名约定推断
4. 处理器类型
	- Controller / ControllerBase
	- MVC 页面控制器 / API 控制器 / 管理后台控制器
5. 返回类型差异
	- IActionResult、ActionResult<T>、JsonResult、FileResult、RedirectResult、ViewResult、ContentResult
	- 这些返回类型会影响后续输出模板、文件下载、重定向、JSON 响应和页面渲染判断

## 参数结构解析（必做）

对每条入口输出以下参数来源与类型信息：

1. Path 参数
	- 来自路由模板占位，如 {id}、{slug}、{version:apiVersion}
	- 必须输出参数名、约束、可空性、默认值
2. Query 参数
	- [FromQuery]、默认简单类型绑定、分页/排序/过滤参数
3. Body 参数
	- [FromBody]、JSON / XML / protobuf / 自定义 input formatter
	- 对复杂对象必须展开字段结构，而不是只写 DTO 类型名
4. Form 参数
	- [FromForm]、表单字段、multipart 表单字段
5. Header 参数
	- [FromHeader]、认证头、版本头、签名头、租户头、自定义上下文头
6. Service 参数
	- [FromServices] 不是用户可控输入，但必须标注为服务注入，避免与用户输入混淆
7. File 参数
	- IFormFile、IFormFileCollection、文件列表、流式上传对象
8. 自定义绑定
	- 自定义 ModelBinder、TypeConverter、BindAsync、TryParse、自定义 input formatter
	- 若参数由这些机制绑定，必须记录绑定器来源和转换规则

## 需要特别识别的 Controller 细节（必做）

1. Model Binding 规则
	- [ApiController] 自动 400、复杂对象默认绑定源、简单类型默认 query/route 绑定
	- BindRequired、BindNever、ValidateNever、BindProperty、TryUpdateModel
2. 上传参数
	- IFormFile / IFormFileCollection / List<IFormFile> / 嵌套 DTO 中的文件属性
3. 版本化
	- [ApiVersion]、MapToApiVersion、URL segment、query/header/media type 版本来源
4. 区域与后台入口
	- [Area]、Admin/Manage/BackOffice 等后台模块路径
5. 自定义动作选择
	- ActionName、NonAction、RemoteService、自定义约定或框架封装生成的 action
6. 输出模板差异
	- FileResult：需要给出下载型模板
	- RedirectResult：需要给出跳转型模板
	- JsonResult / ActionResult<T>：需要给出 JSON 型模板
	- ViewResult：需要给出页面请求模板并标注模板渲染输出面

## 每条入口必须输出

- route_id
- 入口类型（HTTP / HUB / GRAPHQL / WCF）
- 方法与路径或操作名
- 处理器位置
- 参数来源（Route / Query / Body / Header / Cookie / File / Message）
- 完整请求模板或调用模板

对于 HTTP Controller / API 入口，还必须额外输出：

- Controller 名称
- Action 名称
- 路由声明方式（Attribute / Conventional / Mixed）
- API 版本信息（若有）
- Area（若有）
- 参数绑定来源明细（FromRoute / FromQuery / FromBody / FromForm / FromHeader / FromServices / CustomBinder）
- 返回类型模板类别（JSON / File / Redirect / View / Content）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（覆盖完整性确认）**：输出前必须确认入口未被按“高危优先”裁剪。
- 🔴 **CHECKPOINT B（路由闭合确认）**：必须确认 Controller/Action 与最终路径、方法、route_id 一一对应。
- 🔴 **CHECKPOINT C（参数绑定确认）**：必须确认关键入口的绑定来源与返回类型模板已展开。
- 🛑 **STOP**：若存在未映射入口或 route_id 不一致，禁止宣告 route mapping 完成。
- 🔴 **CHECKPOINT D（计数对账自检）**：routes 文件计数对账节齐备（declared_route_count / expanded_route_count / count_self_check）；count_self_check=FAIL 时禁止进入 route-tracer，先修正计数。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| Controller/Action 到最终路径映射不闭合 | 回补 attribute + conventional 组合证据 | 标记为未完成并输出缺失入口清单 |
| 参数绑定来源展开不完整 | 补齐 FromRoute/Query/Body/Form/Header/Services | 暂不下游联动，先保留待补图项 |
| route_id 与下游产物不一致 | 先修复 routes/params 编号一致性 | 禁止继续 trace 阶段并输出修复步骤 |

🔴 **STOP：任一兜底触发时，禁止宣告 route mapping 完成。**

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）、`skills/shared/DOTNET_SINK_REFERENCE.md`（Sink 类型与 trace-gate 校验基准）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
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

- 反模式：仅输出“高危接口”子集。正确做法：强制输出完整入口清单。
- 反模式：省略 Controller 级与 Action 级路由组合。正确做法：展开最终路径并给出来源证据。
- 反模式：把 FromServices 当作用户输入。正确做法：显式区分可控输入与服务注入。
- 反模式：route_id 漂移后继续下游分析。正确做法：先修复映射一致性再继续。

## 处理器位置（必做）

每条入口必须给出处理器来源证据：

- 文件路径
- 类名、方法名、签名
- 若是 Controller，则必须给出 ControllerClass.ActionMethod 形式
- 若路径来自 conventional route，必须给出 Program.cs / Startup.cs 中对应 route 模板位置
- 若由框架约定生成，应说明约定来源而不是只给最终路径

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

## 输出格式（强制）

- routes_{timestamp}.md、params_{timestamp}.md、quality/route_mapper_validation_{timestamp}.md 的标准骨架以 shared/DOTNET_ROUTE_OUTPUT_TEMPLATES.md 为准
- 本 Skill 仅为 HTTP / Controller 类入口分配 route_id：使用 routes_{timestamp}.md 中 === [N] ... === 的 N 作为 route_id，并要求其与 params_{timestamp}.md、route_tracer/{route_id}/trace_{timestamp}.md 和最终汇总报告保持一致
- CLI / hook / sink-only 等非 HTTP 合成入口不占用本文件的 [N] 序号；这类合成 route_id 由 dotnet-audit-pipeline 消费的 cross_analysis/high_risk_routes_{timestamp}.md 统一承载，供后续 route-tracer 分桶使用
- 如项目需要额外字段，可附加在标准骨架后，但不得删除共享模板定义的核心章节与关键字段

### 返回模板差异（强制）

对于 Controller / API Action，必须根据返回类型选择模板：

1. JsonResult / ActionResult<T>
	- 输出标准 HTTP/JSON 请求模板
2. FileResult / PhysicalFileResult / VirtualFileResult
	- 输出下载型请求模板，并标注下载文件名、内容类型、路径来源
3. RedirectResult / LocalRedirectResult / RedirectToActionResult
	- 输出触发重定向的请求模板，并标注可能影响的 ReturnUrl / next 参数
4. ViewResult / PartialViewResult
	- 输出页面请求模板，并标注该 Action 会进入视图渲染链
5. ContentResult
	- 输出普通文本或自定义内容类型请求模板

## 输出前自检（强制）

- [ ] routes 与 params 中每条 Controller / Action 入口的 route_id 一致
- [ ] 没有出现省略占位符
- [ ] Controller 级与 Action 级路由组合已展开
- [ ] Conventional Routing 与 Attribute Routing 并存场景已写出最终路径和来源证据
- [ ] Area、API Versioning、ControllerBase vs Controller 已区分
- [ ] 参数绑定来源已细化到 FromRoute / FromQuery / FromBody / FromForm / FromHeader / FromServices / CustomBinder
- [ ] 文件上传参数 IFormFile / IFormFileCollection 已单独列出
- [ ] 返回类型模板差异已体现到请求模板说明中