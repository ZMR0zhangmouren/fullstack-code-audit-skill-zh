---
name: dotnet-expr-audit
description: .NET 表达式注入审计工具。识别 Roslyn Scripting、Dynamic LINQ、DataTable.Compute、自定义规则引擎中的表达式求值风险。
---

# .NET 表达式注入审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与脚本引擎、表达式解释器、规则引擎、动态 LINQ 和计算表达式相关的共享抓手
- 若项目存在 RuleEngine、FormulaService、ScriptHost、QueryExpressionBuilder 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐表达式入口、参数绑定与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充宿主、规则引擎注册与运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- CSharpScript.EvaluateAsync / RunAsync：用户输入是否进入表达式字符串
- Dynamic LINQ（System.Linq.Dynamic.Core）：Where/OrderBy/Select 接受字符串表达式
- DataTable.Compute / DataTable.Select：filter 或 expression 参数来源
- NCalc / 自定义规则引擎：表达式字符串的可控性与沙箱限制
- 管理后台规则配置、报表公式、营销条件、工作流引擎中的表达式入口
- 表达式求值结果是否进入敏感语义（数据库查询、文件操作、反射调用）
- 沙箱策略：允许访问的类型/命名空间/方法是否足够严格

## 证据引用

- EVID_EXPR_EVAL_ENTRY
- EVID_EXPR_EXPR_CONTROL
- EVID_EXPR_EXEC_CHAIN_ENTRY

## 枚举规则（强制细化）

- 枚举 Roslyn CSharpScript、DataTable.Compute、Dynamic LINQ、NCalc、自定义规则引擎、工作流表达式引擎
- 优先搜索 evaluate、compile、script、expression、formula、rule、condition、where、sort expression 等关键字段
- 枚举管理后台规则配置、报表公式、营销规则、流程引擎、搜索排序、自定义过滤器中的表达式入口
- 对每个表达式入口记录：表达式来源、允许访问的类型/函数、沙箱策略、求值结果流向的敏感语义

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **表达式字符串可控性** | 读取表达式字符串构造源码，确认是否来自用户输入（如 `CSharpScript.EvaluateAsync(userInput)`） | 用户输入直接进入表达式字符串 → 🔴 高危；固定表达式模板 + 仅参数值可控 → 🟠 需确认参数位边界 |
| **沙箱/类型白名单** | 读取 `ScriptOptions` / 自定义沙箱配置，确认允许访问的类型、命名空间、方法是否为 fail-close | 严格白名单且未知类型拒绝 → ✅ 安全；黑名单或无限制 → 🔴 高危；沙箱配置不可见 → ⚠️ 待确认 |
| **编译/求值前校验** | 确认表达式求值前是否有白名单、长度限制、语法限制或 AST 校验 | 有校验且 fail-close → ✅ 安全；仅有长度限制无语法限制 → ⚠️ 可绕过；无校验 → 🔴 高危 |
| **Dynamic LINQ 字符串表达式** | 确认 `System.Linq.Dynamic.Core` 的 `Where`/`OrderBy`/`Select` 是否接受用户可控字符串 | 用户可控且无白名单 → 🔴 高危；固定表达式结构 + 仅值位参数化 → 🟠 需确认 |
| **DataTable.Compute / Select** | 确认 `Compute` 或 `Select` 的 expression/filter 参数是否来自用户输入 | 用户可控 → 🔴 高危；固定表达式 → ✅ 安全 |
| **求值结果敏感语义** | 追踪表达式求值结果是否进入数据库查询、文件操作、权限判断、命令执行等敏感语义 | 进入敏感语义 → 🔴 高危放大；仅用于数值计算且结果不回显 → 🟠 需确认 |

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

1. 用户可控输入直接进入表达式字符串求值（如 `CSharpScript.EvaluateAsync(userInput)`），且无沙箱/白名单
2. `System.Linq.Dynamic.Core` 的 `Where`/`OrderBy`/`Select` 接受用户可控字符串表达式
3. `DataTable.Compute` / `DataTable.Select` 的 expression/filter 参数来自用户可控输入
4. 沙箱/类型白名单为 fail-open 或 silent-fallback，可通过反射、文件操作、进程启动等危险类型绕过
5. 嵌套/递归结构（如多层 RuleEngine 封装）中顶层存在校验，但子层未执行同级校验
6. 表达式求值结果进入数据库查询、文件操作、权限判断等敏感语义

### 待确认

1. 上下文显示可疑模式（如 `EvaluateAsync` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如沙箱配置）存在，但当前分支是否调用、配置是否生效无法确认
3. 异步 / 队列 / 事件链路（如后台规则引擎）中的参数传递未闭合
4. 表达式来源复杂（如从数据库/缓存读取），无法确认是否可被用户影响

### 误报

1. 最终表达式来自固定常量 / 枚举映射，未知输入会拒绝执行（fail-close）
2. 递归所有层级均复用同一 fail-close 类型白名单/沙箱校验器
3. 用户输入仅进入数值参数位，表达式结构完全固定且无字符串插值
4. 表达式求值在严格沙箱中执行，且沙箱禁止访问所有危险类型和方法

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造表达式注入 payload（如 `File.ReadAllText("/etc/passwd")`、`Process.Start("calc")`、`1; DROP TABLE`），验证表达式执行确实存在
- **负向测试**：构造被 barrier 拦截的输入（如沙箱外类型、超长表达式、非法语法），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。


## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（求值入口确认）**：必须先定位真实表达式求值 API。
- 🔴 **CHECKPOINT B（可控性确认）**：必须确认表达式字符串或参数上下文是否可控。
- 🔴 **CHECKPOINT C（执行链确认）**：必须说明求值结果是否进入敏感语义。
- 🛑 **STOP**：若仅有表达式关键字命中但无执行链证据，结论降级为 `⚠️待验证`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 未定位真实求值 API | 回到入口补齐 Evaluate/Compile 调用证据 | 降级 `⚠️待验证`，保留命中点 |
| 表达式可控性无法证明 | 追踪输入到表达式字符串/上下文映射 | 仅输出待验证路径，不做强结论 |
| 求值结果去向不明 | 追踪到数据库/文件/权限判断等敏感语义 | 若仍未闭合，维持保守风险描述 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认注入”。**

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

- 反模式：仅命中 `expression` 关键字就判注入。正确做法：确认求值 API 与可控表达式字符串。
- 反模式：忽略沙箱/白名单配置。正确做法：核查可访问类型与函数边界。
- 反模式：不追踪求值结果去向。正确做法：补齐到敏感语义的后续链路。
- 反模式：证据不足下强结论。正确做法：降级 `⚠️待验证` 并列缺失证据。

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

- vuln_audit/expr_{timestamp}.md
- 可选：vuln_poc/expr_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
