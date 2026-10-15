---
name: dotnet-dom-xss-audit
description: .NET DOM-XSS 审计工具。识别 Blazor JavaScript 互操作、IJSRuntime 调用、前端框架中的客户端 XSS 风险，从 XSS 专项拆分。
---

# .NET DOM-XSS 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与前端输出、JavaScript 执行上下文、URL 解析、DOM 操作、Blazor JSInterop 相关的共享抓手
- 若项目存在 JSBridge、BlazorInterop、DynamicComponentRenderer、ClientTemplateRenderer 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐页面入口、参数来源与 `route_id`）
- 可选：`framework_audit/blazor_{timestamp}.md`（用于补充 Blazor JSInterop 配置与安全控制面）
- 可选：`vuln_audit/xss_{timestamp}.md`（DOM-XSS 与服务端 XSS 存在交叉，可复用部分发现）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

### Blazor JavaScript 互操作
- IJSRuntime.InvokeAsync 调用：JS 方法名、参数来源、是否传递用户输入
- DotNet.invokeMethodAsync、DotNet.invokeMethod 的反射调用
- JSRuntime.SetTonicInitialValueAsync 与组件状态同步
- Blazor Server prerender 期间的 JS 调用与状态注入
- CustomElement、WebComponent 封装中的 JS 桥接

### JavaScript Sink 点
- eval()、setTimeout/setInterval (字符串形式)
- innerHTML、outerHTML、insertAdjacentHTML
- document.write、document.writeln
- location.* (href, pathname, search, hash)
- eval、Function 构造函数
- setAttribute/on* 事件处理器
- postMessage 回调

### URL 位置管理
- window.location、document.URL、document.documentURI
- location.hash、location.search、location.pathname
- URLSearchParams、new URL() 解析
- History API (pushState, replaceState)
- referrer、cookie 值进入脚本

### 前端框架安全
- React: dangerouslySetInnerHTML、eval
- Vue: v-html、$refs 访问
- Angular: bypassSecurityTrustHtml/Url/Script
- jQuery: .html()、.append()、.after()
- 组件库：富文本编辑器、Markdown 渲染器

### 数据流追踪
- C# 服务端到客户端的数据传递（JsonSerializer、WebAssembly 序列化）
- Blazor 的 RenderTreeBuilder 动态构建
- PersistentComponentState 与 OnAfterRender 中的数据使用
- JavaScript 端点的数据回填

## 枚举规则（强制细化）

- 枚举所有使用 IJSRuntime、IJSInProcessRuntime 的 C# 文件
- 优先搜索 InvokeAsync、InvokeVoidAsync、InvokeMethodAsync、DotNet.invokeMethod、SetTonicInitialValueAsync 等关键调用
- 枚举 JavaScript 文件中的 Sink 点：eval、innerHTML、document.write、location、postMessage
- 枚举 URL 参数、路由参数、Cookie、localStorage、sessionStorage 进入脚本的位置
- 枚举 Blazor prerender 阶段、OnParametersSet、OnAfterRender 中的数据使用
- 枚举前端框架特定的危险 API 使用
- 对每个 Sink 点记录：数据来源、Sink 类型、是否经过编码、前端框架二次渲染

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **DOM Sink 可控性** | 确认 `innerHTML`/`document.write`/`eval`/`location` 等 sink 的数据来源是否来自用户可控输入（URL/hash/postMessage/storage） | 用户可控数据直接进入 sink → 🔴 高危；数据来源固定且不可控 → ✅ 安全 |
| **Blazor JSInterop 边界** | 确认 `IJSRuntime.InvokeAsync` 的参数是否来自用户输入，JS 端是否对参数做校验 | 用户输入直接传入 JS 且无校验 → 🔴 高危；有校验层且 fail-close → ✅ 安全 |
| **URL 解析与导航** | 确认 `location.href`/`location.replace` 的目标是否来自用户可控输入，是否限制协议 | 允许 `javascript:`/`data:` 协议 → 🔴 高危；限制为 http/https → ✅ 安全 |
| **postMessage 来源校验** | 确认 `window.addEventListener('message')` 回调是否校验 `event.origin` | 无 origin 校验 → 🔴 高危；严格 origin 白名单 → ✅ 安全 |
| **前端框架安全边界** | 确认 React/Vue/Angular 是否使用危险 API（`dangerouslySetInnerHTML`/`v-html`/`bypassSecurityTrustHtml`） | 使用危险 API 且内容可控 → 🔴 高危；使用安全 API → ✅ 安全 |
| **CSP / Trusted Types** | 确认 CSP 是否配置，是否限制内联脚本，Trusted Types 是否启用 | CSP 严格 + Trusted Types → ✅ 安全；无 CSP 或 CSP 宽松 → 🟠 需确认 |

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

1. 用户可控输入（URL/hash/postMessage/storage）直接进入 `innerHTML`/`document.write`/`eval`/`location` 等 DOM sink
2. Blazor JSInterop 将用户可控输入直接传入 JS 端，且 JS 端无校验
3. `postMessage` 回调未校验 `event.origin`，可接收恶意域消息
4. 前端框架使用 `dangerouslySetInnerHTML`/`v-html`/`bypassSecurityTrustHtml` 且内容可控
5. 嵌套/递归结构（如多层 JSBridge 封装）中顶层存在校验，但子层未执行同级校验

### 待确认

1. 上下文显示可疑模式（如 `eval` 调用），但数据来源不清晰（需补 trace）
2. Barrier 函数（如 origin 校验）存在，但当前分支是否调用无法确认
3. 异步 / 事件链路（如 WebSocket 消息处理）中的数据传递未闭合
4. 前端框架二次渲染边界不可见

### 误报

1. 最终数据来源固定（如硬编码字符串），用户无法控制
2. 递归所有层级均复用同一 fail-close origin 白名单/输入校验器
3. DOM sink 使用的是安全 API（`textContent`/`innerText`）
4. CSP 严格配置 + Trusted Types 启用，且无可绕过路径

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造 DOM-XSS payload（如 `#<img src=x onerror=alert(1)>`、`javascript:alert(1)`、恶意 postMessage），验证漏洞确实存在
- **负向测试**：构造被 barrier 拦截的输入（如非法 origin 被拒绝、危险协议被拦截），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

### 强制记录字段

| 字段 | 说明 |
|------|------|
| file_path | 源文件路径 |
| line_number | 行号 |
| sink_type | DOM Sink 类型（eval/innerHTML/location 等） |
| data_source | 数据来源（URL/param/JS interop/数据库） |
| encoding_applied | 是否应用编码 |
| framework | 使用的前端框架 |
| risk_level | 风险等级（P0-P4） |

## 证据引用

- EVID_DOM_XSS_SINK（新增）：DOM XSS 接收点
- EVID_DOM_XSS_SOURCE（新增）：DOM XSS 源（URL/用户输入）
- EVID_XSS_OUTPUT_POINT：复用 XSS 专项的输出点证据
- EVID_XSS_USER_INPUT_INTO_OUTPUT：复用 XSS 专项的用户输入到输出证据

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 命中 DOM Sink 但 source 不可追踪 | 输出 sink 与上下文证据 | 标记 `⚠️source待验证`，降级 PARTIAL |
| source 可控但缺少执行上下文（编码/CSP） | 记录编码与 CSP 配置证据 | 不输出已确认可利用，转环境依赖 |
| 仅发现框架危险 API，缺少业务可达路径 | 输出 API 命中与页面入口 | 归为潜在风险，待 route-tracer 补证 |
| 与服务端 XSS 证据边界冲突 | 保留冲突证据并分层归档 | 降级并等待 xss/dom-xss 交叉复核 |

🔴 **STOP：缺少“source→sink→执行上下文”三段证据时，禁止输出已确认 DOM-XSS。**

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

| # | 反模式 | 为什么不要做 | 正确做法 |
|---|---|---|---|
| 1 | 把服务端 XSS 直接算作 DOM-XSS | 漏洞面不同 | 明确区分浏览器端与服务端证据 |
| 2 | 只看 sink 不看 source | 无法判断可利用性 | 同步追踪输入来源 |
| 3 | 忽略编码和 CSP | 结论强度会被夸大 | 记录防护上下文后再分级 |

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（DOM Sink确认）**：必须确认 innerHTML/document.write/eval 等 sink 枚举完整。
- 🔴 **CHECKPOINT B（输入可控确认）**：必须确认 URL/hash/postMessage/storage 等输入面可控性。
- 🔴 **CHECKPOINT C（防护有效性确认）**：必须确认清洗、CSP、Trusted Types 等真实生效。
- 🛑 **STOP**：若 sink 与输入链未闭合，不得下“不可利用”结论。

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

- vuln_audit/dom_xss_{timestamp}.md
- 可选：vuln_poc/dom_xss_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC）

### vuln_audit/dom_xss_{timestamp}.md 结构

```markdown
# DOM-XSS 审计报告

## 概述
- 审计范围：`source_path`
- 审计时间：{timestamp}
- 发现的 DOM-XSS 风险点数量：N

## 高风险发现（EVID_DOM_XSS_* 证据引用）
...逐项列出，含文件路径、行号、漏洞描述、风险等级...

## 中风险发现
...逐项列出...

## 低风险发现
...逐项列出...

## Blazor JSInterop 风险点
...专门列出 IJSRuntime 相关发现...

## 前端框架 Sink 点
...枚举 React/Vue/Angular/jQuery 等框架的危险 API 使用...

## 项目内 JS 互操作封装
...项目特定的二次封装...

## DOM-XSS Payload 参考
### 基于 URL
javascript:alert(1)
data:text/html,<script>alert(1)</script>

### 基于 location
<a href="javascript:...">...</a>
window.location=用户输入

### 基于 postMessage
window.addEventListener('message', e => eval(e.data))

### 基于 eval
eval(window.name)
setTimeout用户输入, 100)

### 基于 innerHTML
element.innerHTML = 用户输入

## 修复建议
1. 使用安全的 DOM 操作 API（textContent、innerText）
2. 避免 eval/Function/innerHTML 处理用户输入
3. 对 URL 来源数据使用 URL encoding
4. 配置 CSP 限制内联脚本
5. Blazor 场景：使用 ElementReference 而非字符串回填
```

## 与 XSS 专项的边界划分

- **本 Skill 职责**：客户端 DOM 操作、JavaScript 执行上下文、Blazor JSInterop、URL 解析进入脚本
- **dotnet-xss-audit 职责**：服务端渲染、Razor 输出、ViewData/Model 进入 HTML、HTTP 响应注入
- **核心区别**：本 Skill 关注浏览器端的 JavaScript 执行；XSS 专项关注服务端的 HTML/响应生成
- **交叉场景**：服务端通过 IJSRuntime 传递数据到客户端时，两专项需协同覆盖完整数据流