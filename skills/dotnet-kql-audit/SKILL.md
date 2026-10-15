---
name: dotnet-kql-audit
description: .NET KQL（Kusto Query Language）注入审计工具。识别 Azure Monitor Query SDK、Application Insights SDK、Log Analytics API 中的 KQL 字符串拼接与注入风险，输出分级、PoC 与修复建议。
---

# .NET KQL 注入审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 KQL 相关的入口定义、绑定与转换、前置控制、敏感操作、安全配置抓手
- 若项目存在 KQL Builder、Query Helper、LogAnalyticsClient 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充 Azure Monitor 配置、序列化配置和运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `LogsQueryClient.QueryWorkspaceAsync`、`QueryWorkspace`、`QueryResource`、`MetricsQueryClient` 的调用点与 KQL 查询字符串来源
- 通过字符串拼接、插值字符串、StringBuilder、FormattableString、AppendFormat、Join 生成 KQL 的路径
- `Azure.Monitor.Query` SDK 中 `QueryWorkspace` / `QueryResource` / `QueryWorkspaceAsync` 的参数化边界
- `Microsoft.ApplicationInsights` 中 `TelemetryClient.Query` / `AnalyticsClient` 的查询构造点
- `Microsoft.Azure.OperationalInsights`（旧版）中 `OperationalInsightsDataClient.Query` 的调用点
- 动态表名、列名、where 条件片段、extend/project 字段、`| take` 分页片段等"无法参数化"的动态片段是否有白名单
- KQL 管道注入：通过 `\n` 注入额外管道操作（如 `| take 10000` 变成 `| take 10000\n| union (traces | take 10000)`）
- `extend`、`project`、`where`、`contains`、`has`、`startswith` 等 KQL 运算符中混入未校验字符串
- 多租户、资源范围过滤器是否被动态 KQL 绕过
- 异常处理、日志和调试输出中是否暴露完整 KQL、查询参数和 workspace/resource ID

## 枚举规则（强制细化）

- 枚举所有继承 Controller / ControllerBase、Service、Background Job、GraphQL Resolver、Hub 中的 KQL 调用点
- 优先搜索 `LogsQueryClient`、`QueryWorkspace`、`QueryResource`、`MetricsQueryClient`、`QueryWorkspaceAsync`、`OperationalInsightsDataClient`、`AnalyticsClient`、`TelemetryClient.Query`
- 枚举字符串拼接、插值字符串、StringBuilder、FormattableString、AppendLine、Join、Format、KQL helper 的使用位置
- 单独枚举"不可参数化片段"：动态表名、列名、where 条件、extend/project 字段、`| take` / `| limit` 分页、union/join 目标表
- 枚举 KQL Builder、Query Helper、LogAnalyticsClient、自定义 KQL 构造器的封装链路
- 对每个调用点记录：KQL 来源、参数对象来源、调用栈上游入口、是否在资源范围过滤器/多租户过滤下执行

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **KQL 字符串拼接** | 读取 KQL 查询字符串构造源码，确认是否来自字符串拼接/插值（如 `$"traces | where message contains '{input}'"`） | 外部可控输入参与 KQL 字符串拼接 → 🔴 高危；固定 KQL 模板 + SDK 参数化值位 → 🟠 需确认参数化边界 |
| **SDK 参数化边界** | 确认 `QueryWorkspaceAsync` / `QueryResource` 是否正确使用 SDK 的参数化能力，而非将用户输入直接拼入 KQL 字符串 | 正确使用 SDK 参数化且无插值混入 → ✅ 安全；SDK 调用但 KQL 字符串含插值 → ⚠️ 待确认 |
| **动态表名/列名白名单** | 确认动态表名、列名、extend/project 字段、`| take` / `| limit` 分页是否来自白名单映射 | fail-close 白名单 → ✅ 安全；黑名单或无白名单 → 🔴 高危；白名单实现不可见 → ⚠️ 待确认 |
| **KQL 管道注入** | 确认 KQL 字符串构造后是否允许换行追加管道操作（如注入 `\n| union (traces)`） | 允许换行追加管道 → 🔴 高危；严格单查询且无可控管道位 → ✅ 安全 |
| **运算符可控性** | 确认 `where`、`contains`、`has`、`startswith`、`extend`、`project` 等运算符中的值位是否来自用户可控输入 | 值位可控且无转义/白名单 → 🔴 高危；值位来自固定常量或已验证白名单 → ✅ 安全 |
| **多租户/资源范围过滤器** | 确认多租户/资源范围过滤器是否被动态 KQL 绕过（如通过 union 跨 workspace 查询） | 过滤器可被动态 KQL 绕过 → 🔴 高危；过滤器在查询构造前锁定且不可被 KQL 覆盖 → ✅ 安全 |

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

1. 用户可控输入直接进入 KQL 字符串拼接/插值位置，且无 barrier 验证
2. 动态表名、列名、extend/project 字段、`| take` 分页片段无白名单或白名单为 fail-open
3. KQL 字符串构造允许换行追加管道操作，导致管道注入可行
4. `where` / `contains` / `has` 等运算符的值位来自用户可控输入且无转义/白名单
5. 嵌套/递归结构（如多层 KQL Builder 封装）中顶层存在校验，但子层未执行同级校验

### 待确认

1. 上下文显示可疑模式（如 `QueryWorkspaceAsync` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如 KQL 参数化封装）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路（如后台任务定时查询 Log Analytics）中的参数传递未闭合
4. SDK 参数化与字符串拼接混用，但当前调用点无法确认具体使用路径

### 误报

1. 最终 KQL 查询来自固定常量 / 模板映射，未知输入会拒绝执行（fail-close）
2. 递归所有层级均复用同一 fail-close 白名单校验器（表名/列名/extend 字段）
3. 用户输入仅进入 SDK 参数化值位，KQL 字符串模板完全固定且无插值
4. 多租户/资源范围过滤器在查询构造前锁定，不可被 KQL 覆盖

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造 KQL 注入 payload（如 `evil' | union (traces)`、`message contains 'x'\n| union (traces | take 100)`、非法 extend 字段），验证注入确实存在
- **负向测试**：构造被 barrier 拦截的输入（如白名单外表名、非法列名、非参数化值位），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 证据引用（强制）

- EVID_KQL_EXEC_POINT
- EVID_KQL_STRING_CONSTRUCTION
- EVID_KQL_USER_PARAM_TO_KQL_FRAGMENT

## 执行检查点

🔴 **STOP — 输出结论前必须核对以下两项，缺一不得继续：**

1. **trace-gate 检查**：若 `route_tracer/{route_id}/trace_{timestamp}.md` **不存在或 trace_status=PARTIAL/UNRESOLVED**，所有结论必须降级为 `⚠️待验证`，禁止输出 `✅已确认可利用`。
2. **EVID 完整性检查**：若 EVID_KQL_EXEC_POINT / EVID_KQL_STRING_CONSTRUCTION / EVID_KQL_USER_PARAM_TO_KQL_FRAGMENT 三者未全部满足，禁止输出高危（🔴）级别结论。

🔴 **STOP — 发现以下任意情况时，必须在输出中单独标注，不得静默略过：**

- 动态片段（表名/列名/extend 字段/where 条件）无白名单保护 → 单列一条 `⚠️ 白名单缺失风险`
- 多租户/资源范围过滤器被动态 KQL 绕过 → 单列一条 `⚠️ 过滤器绕过风险`
- 异常/日志中泄露完整 KQL 或查询参数 → 单列一条 `⚠️ 信息泄露风险`

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每个 skill 至少维护 2 个典型测试用例（happy path + 一条复杂场景），并在结果中标注用例 ID。
- 每轮评估至少 1 条用例执行 `full_test`；若受限只能 `dry_run`，必须记录 `dry_run_reason` 与补测计划。
- 通过标准至少同时满足：`意图达成`、`关键证据命中`、`输出格式合规`；任一不满足不得给出"通过"。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如"首先/其次/最后/综上/说白了/换句话说"）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出"确认可利用/可交付"。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

| # | 反模式 | 为什么错 | 正确做法 |
|---|---|---|---|
| 1 | **无 trace 时输出 ✅已确认** | 仅凭静态抓手无法证明参数可控性与执行路径 | 降级为 `⚠️待验证`，说明缺失证据 |
| 2 | **SDK 参数化接口直接判定为安全** | `QueryWorkspaceAsync(workspace, $"traces | where message contains '{userInput}'")` 仍为注入风险；SDK 参数化 ≠ KQL 无注入 | 检查 KQL 字符串是否通过插值混入，而非仅看 SDK 调用方式 |
| 3 | **只搜一层调用，忽略封装链** | 业务层调 KQL Builder，KQL Builder 调 `QueryWorkspaceAsync`——漏洞在最底层 | 枚举规则要求追踪到最终执行点 |
| 4 | **动态表名/列名/extend 字段当作低危忽略** | 表名/列名注入可用于 union-based 攻击、跨表数据泄露 | 必须单独枚举不可参数化片段并给出白名单建议 |
| 5 | **忽略 KQL 管道注入** | KQL 用 `|` 管道操作，注入 `\n| union (traces)` 可跨表查询 | 枚举时必须检查 KQL 字符串构造后是否允许换行追加管道 |

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按"共享抓手索引 → 本专项枚举规则 → 证据点引用"顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件"输出"章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（KQL 执行入口确认）**：必须确认 KQL 执行入口与 SDK/原生调用边界。
- 🔴 **CHECKPOINT B（KQL 字符串构造确认）**：必须确认 KQL 字符串为参数绑定而非字符串拼接/插值。
- 🔴 **CHECKPOINT C（高危 KQL 片段确认）**：必须确认动态表名、列名、extend/project 字段、管道追加等高危片段。
- 🛑 **STOP**：若参数化证据与执行链未闭合，不得输出"无注入风险"结论。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| trace 不完整或缺失 | 回补 route_tracer 证据并对齐 route_id | 降级 `⚠️待验证`，禁止已确认可利用 |
| 参数到 KQL 片段映射不闭合 | 补齐字符串构造与执行点链路证据 | 不输出高危确认，仅给验证步骤 |
| 动态片段白名单证据不足 | 逐项核对表名/列名/extend 字段白名单逻辑 | 保守标记高风险待验证项 |

🔴 **STOP：任一兜底触发时，禁止输出"无注入风险"。**

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如"可能有风险/建议关注/视情况而定/大概率"等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

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

- vuln_audit/kql_{timestamp}.md
