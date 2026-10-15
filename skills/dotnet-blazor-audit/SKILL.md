---
name: dotnet-blazor-audit
description: Blazor 框架专项审计工具。针对 Blazor Server 与 Blazor WebAssembly 的状态同步、组件输出、JSInterop、认证状态和 API 边界进行白盒审计。
---

# Blazor 框架专项审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 blazor 相关的入口定义、绑定转换、前置控制、敏感操作、安全配置抓手
- 若项目存在框架二次封装、统一扩展方法、平台基座或宿主包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（如已由 `dotnet-route-mapper` 生成，用于对齐页面/API 入口、参数绑定与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（如需对齐组件级授权、页面级授权与后端 API 授权边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（如需把组件事件、后端 API 调用和服务端副作用链做交叉引用）

## 重点检查

- Blazor Server 事件处理、组件生命周期、Circuit 重连、状态同步与服务端副作用入口
- MarkupString、RenderFragment、动态组件、参数级联、模板组件和第三方 UI 组件的输出边界
- JSInterop 输入输出信任边界、浏览器本地存储、剪贴板、文件访问、导航与前端脚本互操作
- Blazor WebAssembly 客户端代码暴露、令牌持有、API 调用链、离线缓存和 source map 泄露
- 身份认证状态提供器、租户上下文、组件级授权、页面级授权与后端 API 授权是否一致
- 预渲染、静态 SSR、交互式渲染混用时的状态泄露与双重执行问题

## 枚举规则（强制细化）

- 枚举所有 .razor 组件、页面路由、事件处理器、生命周期方法、AuthorizeView、CascadingParameter、JSInvokable 与 JSRuntime 调用点
- 优先搜索 @page、@onclick、NavigationManager、MarkupString、RenderFragment、AuthorizeView、AuthenticationStateProvider、IJSRuntime、ProtectedLocalStorage、ProtectedSessionStorage
- 区分 Blazor Server、Blazor WebAssembly、交互式 SSR、预渲染混合模式，记录状态所在端、令牌所在端、是否存在双重执行或状态漂移
- 枚举文件上传、导航重定向、客户端缓存、离线存储、剪贴板和浏览器 API 互操作，记录哪些输入会进入服务端副作用或输出上下文
- 对每个关键组件记录：路由、授权方式、状态依赖、JS 互操作、后端 API 调用、可触发的副作用类型

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 组件/事件入口存在且用户可触发 | 存在 .razor 组件路由、@onclick 事件、JSInvokable 回调且用户可实际触发 | BLOCKED → 无用户可触发的入口，专项降为低优先级 |
| 二级 | 状态同步/JSInterop 存在数据泄露或注入 | MarkupString/RenderFragment/JSRuntime 调用存在未编码输出或参数注入，或状态同步跨 Circuit 泄露 | BLOCKED → 状态同步与 JSInterop 边界安全，结论降级 |
| 三级 | 后端调用链未授权或越权 | 组件触发的后端 API/Hub/服务调用未做业务鉴权，或 Blazor Server/WASM 授权边界不一致 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中组件/事件入口 + 状态同步/JSInterop + 后端调用链，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 组件路由/事件 → 状态同步 → JSInterop 链路；
  2. 验证 MarkupString/RenderFragment/JSRuntime 的编码边界与参数可控性；
  3. 评估后端 API/Hub/服务调用的授权边界与 Blazor Server/WASM 差异；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：组件入口可触发 + 状态同步/JSInterop 存在安全问题 + 后端调用未授权。输出 `确认漏洞`。
2. **待确认**：组件/JSInterop/后端调用证据部分存在，但授权链或状态边界不可证实。输出 `待确认`。
3. **误报/无风险**：组件入口已授权、JSInterop 参数校验严格、后端调用鉴权完整、Server/WASM 边界清晰。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 Blazor 组件（.razor）或 JSInterop 调用
  - 存在用户可触发的组件路由/事件/回调
  - 或 MarkupString/RenderFragment/JSRuntime 存在未编码输出/参数注入
  - 或后端 API/Hub 调用未做业务鉴权
- **测试用例建议**：
  - Happy Path：正常组件渲染与事件处理，状态同步安全，JSInterop 参数校验正确
  - 边界/歧义：Circuit 重连状态漂移、预渲染与交互渲染双重执行、ProtectedLocalStorage 令牌泄露、WASM 客户端代码暴露
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（入口清单确认）**：必须确认组件路由、事件回调、参数绑定入口完整。
- 🔴 **CHECKPOINT B（数据流闭合确认）**：必须确认用户输入到敏感操作的中间链路可追溯。
- 🔴 **CHECKPOINT C（防护证据确认）**：必须确认鉴权、编码、校验等防护证据可落盘。
- 🛑 **STOP**：若入口或证据链未闭合，结论降级为 `⚠️待验证`。

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

- 输出文件：framework_audit/blazor_{timestamp}.md
- 必须按 组件入口、状态与授权、输出与 JS 互操作、客户端暴露面 四个章节组织结果
- 每个问题点必须写明 组件或页面、触发事件、状态来源、渲染上下文、后端调用链或本地存储依赖
- 对 Server 与 WebAssembly 必须分别下结论，不得把服务端状态风险与纯前端暴露风险混为一类

## 证据引用

- EVID_XSS_OUTPUT_POINT
- EVID_AUTH_PATH_PROTECTED_MATCH
- EVID_AUTH_PERMISSION_CHECK_EXEC
- EVID_SESS_COOKIE_FLAGS

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 组件授权可见但后端 API 授权链不完整 | 输出组件级与API级授权证据 | 标记 PARTIAL，禁止越权已确认结论 |
| JSInterop 调用点可见但参数来源不明 | 输出调用点和候选来源 | 降级为待验证并列缺失项 |
| Server/WASM 混合模式边界不清 | 分别记录两端状态与令牌位置 | 结论按模式拆分并降级 |
| 预渲染与交互渲染执行差异不可证实 | 输出生命周期证据与假设 | 标记环境依赖，不给强结论 |

🔴 **STOP：组件状态链与后端调用链未闭合时，不得输出“已确认可利用”结论。**

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
| 1 | 将 Blazor Server 与 WASM 风险混写 | 威胁模型不同 | 必须分端输出结论 |
| 2 | 只看前端组件不看后端副作用 | 无法判定实际影响 | 关联后端 API/服务调用链 |
| 3 | 忽略 JSInterop 参数可控性 | 容易漏掉 DOM/命令链风险 | 必须记录参数来源与去向 |

输出类型映射：XSS、AUTH、LOGIC、CFG、SESS。
