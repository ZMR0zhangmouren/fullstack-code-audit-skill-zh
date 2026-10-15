---
name: dotnet-ssti-audit
description: .NET Server-Side Template Injection（SSTI）审计工具。识别模板引擎配置错误、模板来源可控、用户输入注入与沙箱逃逸风险，从 dotnet-tpl-audit 拆分的独立专项。
---

# Server-Side Template Injection（SSTI）审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与模板注入相关的共享抓手：用户输入处理、模板渲染入口、表达式求值链
- 若项目存在模板引擎二次封装、视图引擎基座或渲染管道包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围
- 本 Skill 从 `dotnet-tpl-audit` 拆分，专注于 SSTI 漏洞检测，不覆盖 TPL 其他检查面

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、鉴权边界或业务前置条件）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充视图引擎配置、模板引擎设置或运行时边界）
- 若属于 trace-gate 专项：优先消费 `route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 若属于静态证据驱动专项：`route_tracer/*` 仅作为交叉证据，不是前置硬依赖

## 重点检查

### 模板引擎识别

- **Scriban**：`Scriban.Scripting.ScriptRuntime` / `Template.Parse()` / `template.Render()`
- **Fluid**：`Fluid.FluidParser` / `Fluid.Template.Parse()` / `template.Render()`
- **Nunjucks.NET**：`Nunjucks.Precompile` / `Environment.RenderString()`
- **Razor**：`@* ... *@` 注释内插、`Render Razor` / `IRazorEngine`
- 其他模板：`DotLiquid.Template` / `Handlebars.NET` / `Mustache`

### 模板来源可控

- 模板文件路径：`Template.Parse(File.ReadAllText(userInput))`
- 模板字符串来源：`Template.Parse(request.Form["template"])`
- 模板名称动态拼接：`template.Parse(GetTemplateName(userInput))`
- 数据库/缓存加载模板后渲染
- Proto 定义中嵌入模板

### 用户输入到模板注入

- 直接渲染用户输入：`template.Render(userInput)`
- 参数注入到模板上下文：`template.Render(new { name = userInput })`
- 嵌套模板包含：模板 A 包含模板 B，用户输入控制 B
- 模板预编译后注入：`CompiledTemplate.Create(userTemplate)`

### Sandbox 逃逸

- Scriban 不安全函数：`@"@{ System.Diagnostics.Process..." }`
- Fluid 无限制对象访问：`model.GetType()` / `model.GetType().GetMethod()`
- 禁用函数绕过：`member access`、`function call` 配置
- 对象构造：`new Object()` 在模板中
- 反射调用链：`GetType().GetMethod().Invoke()`

### 模板引擎配置

- 安全模式配置：`FluidParserOptions` / `ScriptRuntime.Allow(memberAccess: false)`
- 默认安全设置：是否默认禁用危险操作
- 编译缓存：`Template.Compile()` 缓存策略
- 模板沙箱：`IHost` / `IMemberVisitor` 配置

## 枚举规则（强制细化）

### 模板引擎检测

搜索以下关键字并记录引擎类型：

```
// Scriban
Scriban.Template
Scriban.Scripting
Template.Parse
template.Render

// Fluid
Fluid.Template
Fluid.FluidParser
template.Render
FluidParserOptions

// Nunjucks
Nunjucks.Precompile
Environment.RenderString
NunjucksTemplateOptions

// Razor
@* *@
RazorLight
IRazorEngine
```

### 模板来源检测

搜索以下模式并记录模板来源：

```
File.ReadAllText(
File.ReadAllBytes(
request.Form[
request.QueryString[
request.Cookies[
route.Values[
HttpContext.Session
Cache.Get
Redis.Get
```

### 用户输入到渲染链检测

搜索以下模式：

```
template.Parse(userInput
template.Render(
Template.Parse(
ParseAsync(
RenderAsync(
new
```

### Sandbox 配置检测

搜索以下模式并记录配置：

```
AllowMemberAccess
AllowFunctionCall
AllowObjectConstruction
MemberAccess
FunctionInterceptor
SafeMemberAccess
```

### 危险函数调用检测

搜索以下模式：

```
System.Diagnostics.Process
GetType()
GetMethod(
Invoke(
Runtime.GetType
typeof(
Activator.CreateInstance
Assembly.Load
```

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 模板引擎存在且渲染入口可达 | 存在 Scriban/Fluid/Razor 等模板引擎且用户可触发渲染入口 | BLOCKED → 无模板引擎或渲染入口不可达，专项结束 |
| 二级 | 模板来源可控 | 模板字符串/文件名/路径来源包含用户输入（request.Form/QueryString/Cookie/数据库） | BLOCKED → 模板来源硬编码且不可控，结论降级 |
| 三级 | 沙箱可逃逸或危险函数可执行 | 沙箱配置宽松（AllowMemberAccess/AllowObjectConstruction）或模板中可调用 System.Diagnostics.Process/GetType/Invoke 等 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中模板引擎 + 模板来源 + 沙箱/危险函数配置，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 用户输入 → 模板来源（字符串/文件/数据库） → 渲染入口 链路；
  2. 验证模板引擎沙箱配置（AllowMemberAccess/AllowFunctionCall/AllowObjectConstruction）；
  3. 评估模板中是否可调用危险函数（Process.GetType.Invoke/Activator.CreateInstance/Assembly.Load）；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：模板引擎可达 + 模板来源可控 + 沙箱逃逸/危险函数可执行。输出 `确认漏洞`。
2. **待确认**：模板引擎与来源证据部分存在，但沙箱配置或执行链不可证实。输出 `待确认`。
3. **误报/无风险**：模板来源硬编码、沙箱严格禁用危险操作、无用户输入进入模板。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在模板引擎（Scriban/Fluid/Nunjucks/Razor）
  - 模板来源包含用户可控输入
  - 或沙箱配置宽松允许危险操作
- **测试用例建议**：
  - Happy Path：正常模板渲染，模板来源硬编码，沙箱严格限制
  - 边界/歧义：模板字符串注入 `{{ 7*7 }}`、File.ReadAllText 路径穿越、AllowMemberAccess 反射调用、嵌套模板包含注入
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用
```

## 证据引用

- EVID_SSTI_TEMPLATE_SOURCE：模板来源可控性证据
- EVID_SSTI_SANDBOX_ESCAPE：沙箱逃逸证据
- EVID_SSTI_USER_INPUT_TO_TEMPLATE：用户输入到模板注入点证据
- EVID_SSTI_RENDER_EXEC_CHAIN：模板渲染执行链证据
- EVID_TPL_ENGINE_RENDER_OR_PARSE_ENTRY：模板引擎入口证据（跨专项）
- EVID_TPL_TEMPLATE_OR_EXPR_CONTROL：模板名或表达式可控性证据（跨专项）

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 识别到模板引擎但无法确认模板来源 | 先输出渲染入口与上下文参数 | 标记 `⚠️模板来源待验证`，降级为 PARTIAL |
| 模板来源可控但沙箱配置不可见 | 记录可见配置与默认行为假设 | 归入环境依赖，不输出已确认 RCE 结论 |
| 仅有危险函数命中，无执行链闭合 | 补充“输入→模板→执行”链路追踪 | 未闭合时仅列潜在风险 |
| 与 TPL/EXPR 专项证据冲突 | 保留冲突证据并标注来源 | 待交叉复核后再给最终强度 |

🔴 **STOP：缺少模板来源可控性或执行链闭合证据时，禁止输出“已确认 SSTI 可利用”。**

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
| 1 | 见到模板引擎就判 SSTI | 引擎存在不等于输入可控 | 必须证明来源可控与注入路径 |
| 2 | 把 XSS 输出点当 SSTI 执行点 | 风险类型不同 | 区分模板执行与前端渲染 |
| 3 | 未验证沙箱配置就给 RCE 结论 | 结论强度失真 | 先给待验证/环境依赖分级 |

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（模板入口确认）**：必须确认模板渲染入口与引擎类型。
- 🔴 **CHECKPOINT B（表达式可控确认）**：必须确认用户输入是否可进入表达式求值。
- 🔴 **CHECKPOINT C（沙箱隔离确认）**：必须确认函数白名单与执行隔离边界。
- 🛑 **STOP**：若模板执行能力与输入可控性未同时核定，不得下“不可利用”结论。

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

- vuln_audit/ssti_{timestamp}.md
- 必须写明漏洞类型（Scriban/Fluid/Nunjucks/Razor）、注入点、可控性等级、利用链复杂度
- 如发现模板来源完全可控且存在 Sandbox 逃逸，额外输出 `vuln_poc/ssti_{timestamp}.md`（包含 PoC 模板片段）
- 如发现潜在风险但缺少完整数据流追踪，输出到 `待补证风险池` 并标记 `⚠️待验证`

## 与其他专项的联动

- `dotnet-tpl-audit` 覆盖 TPL 其他检查面（模板文件名注入、表达式注入），本 Skill 不重复覆盖
- 本 Skill 发现的渲染链可传递给 `dotnet-route-tracer` 用于完整 trace
- 涉及反射或动态代码生成时，可联动 `dotnet-deser-audit`
- 涉及表达式求值时，可联动 `dotnet-expr-audit`