---
name: dotnet-xss-audit
description: .NET XSS 审计工具。识别 Razor、Blazor、MVC/View 输出上下文中的未编码输出、Raw 输出和 DOM 注入风险。
---

# .NET XSS 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与输出上下文、编码边界、模板渲染、前端组件回显和 JSON/HTML/JS 返回相关的共享抓手
- 若项目存在 HtmlHelper、TemplateRenderer、EmailRenderer、PreviewService 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐输出入口、参数来源与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充 Razor/Blazor/GraphQL/SignalR 等输出上下文控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- Razor 的 Html.Raw、IHtmlContent、TagHelper、Partial、ViewComponent、DisplayTemplate、EditorTemplate 输出边界
- Blazor 的 MarkupString、RenderFragment、动态组件参数、JSInterop 回填和 prerender 混合渲染场景
- ViewData、ViewBag、Model、TempData、Query 参数、API 返回 JSON、数据库内容进入 HTML、属性、JS、CSS、URL 上下文的映射
- 手工拼接 script、onclick、href、style、data-* 属性以及 JSON 序列化后嵌入页面的模式
- 自定义 HtmlEncoder、JavaScriptEncoder、UrlEncoder、禁用编码或使用 UnsafeRelaxedJsonEscaping 的代码路径
- 富文本、Markdown、模板内容、WYSIWYG 编辑器输出和服务端清洗器的 allowlist/denylist 规则
- CSP、Trusted Types、Razor 默认编码、Blazor 组件隔离和前端框架二次渲染是否真实降低影响

## 枚举规则（强制细化）

- 枚举所有 Razor View、Partial、Layout、ViewComponent、TagHelper、Blazor Component、邮件模板、导出 HTML 模板
- 优先搜索 Html.Raw、MarkupString、IHtmlContent、RenderFragment、UnsafeRelaxedJsonEscaping、自定义 Encoder 配置
- 枚举用户输入、数据库字段、富文本内容、CMS 模板、GraphQL 数据、Hub 消息回显到 HTML/属性/JS/URL/CSS 的位置
- 对每个输出点记录：上下文类型、编码方式、是否经过清洗、下游前端框架是否再次解释

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **HTML 上下文编码** | 确认 Razor/Blazor 默认编码器是否生效，用户输入进入 HTML 正文时是否经过 `HtmlEncoder` | 默认编码生效且不可绕过 → ✅ 安全；自定义编码器为 fail-open → ⚠️ 可绕过；使用 `Html.Raw` / `MarkupString` 且无清洗 → 🔴 高危 |
| **属性上下文编码** | 确认 HTML 属性值（如 `href`、`src`、`alt`）中的用户输入是否经过属性编码 | 属性编码生效 → ✅ 安全；未编码直接进入属性值 → 🔴 高危；仅 HTML 编码但非属性编码 → ⚠️ 待确认 |
| **JS 上下文编码** | 确认进入 `<script>` 标签或事件处理器（`onclick` 等）的用户输入是否经过 `JavaScriptEncoder` | JS 编码生效 → ✅ 安全；未编码直接进入 JS 上下文 → 🔴 高危 |
| **URL 上下文编码** | 确认进入 `href`、`src`、`url()` 的用户输入是否经过 `UrlEncoder`，是否允许 `javascript:` / `data:` 协议 | URL 编码生效且禁止危险协议 → ✅ 安全；允许 `javascript:` 协议 → 🔴 高危 |
| **CSS 上下文编码** | 确认进入 `style` 属性或 `<style>` 标签的用户输入是否经过 CSS 编码 | CSS 编码生效 → ✅ 安全；未编码直接进入 CSS → 🔴 高危 |
| **富文本清洗** | 读取富文本清洗器（如 HtmlSanitizer）实现源码，确认是否为 fail-close（仅允许白名单标签/属性） | fail-close 白名单 → ✅ 安全；黑名单模式 → ⚠️ 可绕过；无清洗 → 🔴 高危 |
| **CSP / Trusted Types** | 确认 CSP 头是否配置，是否禁止 `unsafe-inline`，Trusted Types 是否启用 | CSP 严格 + Trusted Types → ✅ 安全；CSP 宽松或缺失 → 🟠 需确认；无 CSP → 🔴 高危放大 |

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

1. 用户可控输入通过 `Html.Raw`、`MarkupString`、未编码输出直接进入 HTML/属性/JS/URL/CSS 上下文
2. 自定义编码器为 fail-open，未知输入默认允许透传
3. 富文本清洗为黑名单模式，可通过未知标签/属性绕过
4. 前端框架（React/Vue/Angular）二次渲染时未对服务端传入数据做编码
5. 嵌套/递归结构（如多层 HtmlHelper 封装）中顶层存在编码，但子层未执行同级编码

### 待确认

1. 上下文显示可疑模式（如 `Html.Raw` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如编码器）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路（如 SignalR 消息推送）中的数据传递未闭合
4. 前端框架二次渲染边界不可见

### 误报

1. 最终输出来自固定常量 / 枚举映射，未知输入会拒绝执行（fail-close）
2. 递归所有层级均复用同一 fail-close 编码器/清洗器
3. 用户输入仅进入已严格编码的值位，且编码器为 fail-close
4. CSP 严格配置 + Trusted Types 启用，且无可绕过路径

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造 XSS payload（如 `<script>alert(1)</script>`、`javascript:alert(1)`、`onerror=alert(1)`、CSS 表达式），验证漏洞确实存在
- **负向测试**：构造被 barrier 拦截的输入（如未知 HTML 标签被清洗、危险协议被拦截、未编码输入被自动编码），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 证据引用

- EVID_XSS_OUTPUT_POINT
- EVID_XSS_USER_INPUT_INTO_OUTPUT
- EVID_XSS_ESCAPE_OR_RAW_CONTROL

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（输出上下文确认）**：必须确认 HTML/属性/JS/URL/CSS 各上下文的编码策略。
- 🔴 **CHECKPOINT B（危险输出确认）**：必须确认 Html.Raw/MarkupString/自定义编码器等危险点。
- 🔴 **CHECKPOINT C（清洗与隔离确认）**：必须确认富文本清洗规则与前端二次渲染边界。
- 🛑 **STOP**：若上下文与编码链未闭合，不得下“已安全”结论。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 输出上下文无法精确分类 | 按 HTML/属性/JS/URL/CSS 分别补齐证据 | 降级 `⚠️待验证` |
| 危险输出点来源不清（Raw/MarkupString） | 回溯到输入源与清洗链 | 不输出“已安全”结论 |
| 前端二次渲染边界不明确 | 补齐 DOM 注入与框架解释路径 | 保守评估并列待补证据 |

🔴 **STOP：任一兜底触发时，禁止输出“已安全”。**

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

- 反模式：把“已编码”作为统一结论。正确做法：按 HTML/属性/JS/URL/CSS 上下文分别验证。
- 反模式：忽略 Html.Raw/MarkupString 风险点。正确做法：逐点核对来源与清洗策略。
- 反模式：只看后端不看前端二次解释。正确做法：评估 DOM 注入与框架再渲染。
- 反模式：证据链未闭合就宣告安全。正确做法：降级并补充验证项。

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

- vuln_audit/xss_{timestamp}.md
- 可选：vuln_poc/xss_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
