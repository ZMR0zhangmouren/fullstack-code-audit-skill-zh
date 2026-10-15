---
name: dotnet-sql-audit
description: .NET SQL 注入审计工具。识别 ADO.NET、Dapper、EF Core RawSQL 和动态查询构造中的注入风险，输出分级、PoC 与修复建议。
---

# .NET SQL 注入审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 SQL 相关的入口定义、绑定与转换、前置控制、敏感操作、安全配置抓手
- 若项目存在 Repository、QueryBuilder、SQL Helper、DbExecutor 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充 ORM、序列化配置和运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致
- 可选（如存在自动化预筛）：`scan_audit/sql_injection_matches_{timestamp}.jsonl`（预筛命中点，用于优先级排序和快速定位）

## 重点检查

- SqlCommand、DbCommand、SqlDataAdapter、ExecuteReader/ExecuteScalar/ExecuteNonQuery 的调用点与命令文本来源
- 通过字符串拼接、插值字符串、StringBuilder、FormattableString、AppendFormat、Join 生成 SQL 的路径
- Dapper Query/Execute、多结果集、匿名对象参数与 DynamicParameters 的参数化边界
- EF Core FromSqlRaw、ExecuteSqlRaw、Database.SqlQueryRaw、迁移脚本与仓储层封装的 RawSQL 执行点
- 排序字段、列名、表名、分页片段、条件片段、IN 列表等“无法参数化”的动态片段是否有白名单
- LINQ 最终是否退化为原始 SQL、表达式树转 SQL 时是否混入未校验字符串
- 多租户、软删除、行级权限过滤器是否被 RawSQL、IgnoreQueryFilters 或自定义仓储绕过
- 异常处理、日志和调试输出中是否暴露完整 SQL、参数值和连接信息

## 枚举规则（强制细化）

- 枚举所有继承 Controller / ControllerBase、Repository、Service、Background Job、GraphQL Resolver、Hub 中的数据库调用点
- 优先搜索 SqlCommand、DbCommand、FromSqlRaw、ExecuteSqlRaw、Query、Execute、SqlQueryRaw、CreateCommand、CommandText
- 枚举字符串拼接、插值字符串、StringBuilder、FormattableString、AppendLine、Join、Format、Raw SQL helper 的使用位置
- 单独枚举“不可参数化片段”：排序字段、列名、表名、where 片段、group by、having、offset/fetch、TOP、IN 列表
- 枚举仓储封装、QueryBuilder、自定义 Specification、Dynamic LINQ 到 RawSQL 的退化链路
- 对每个调用点记录：SQL 来源、参数对象来源、调用栈上游入口、是否在事务/多租户过滤/软删除过滤器下执行

## 证据引用（强制）

- EVID_SQL_EXEC_POINT
- EVID_SQL_STRING_CONSTRUCTION
- EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT

## Barrier 验证（强制，新增）

对每个 sink 中的每个动态参数，必须验证其实际 barrier 行为，**不看函数名，看实际实现**。

### Barrier 验证矩阵

| 参数类型 | 典型 Barrier | 验证要求 |
|---------|-------------|---------|
| LIKE 值 | `escape_like_literal()` / `SqlLikeString` | 读取实际源码：是否处理了 `%`、`_`、`[`、`]` 转义；是否存在 Unicode/UTF-8 绕过；是否处理 ESCAPE 子句 |
| 整数 | `strict_int()` / `int.TryParse()` | 读取实际源码：是否拒绝非数字输入；是否有长度限制；是否验证返回值 |
| ORDER BY 字段 | `allowlisted_sort_key()` / `Enum.Parse<T>()` | 读取实际源码：是否只返回白名单字段；是否有大小写/编码问题；是否有 default 分支且 fail-close；**嵌套/递归调用时子层是否复用同一校验器；子层独立解析时是否单独校验** |
| 列名/表名 | 白名单/映射表/`ValidateColumnName()` | 读取实际源码：是否可绕过；是否区分大小写；是否允许通配符 |
| 嵌套过滤字段 | 递归层统一校验器 | **逐层验证**：顶层校验+子层未校验→⚠️ 高风险；所有层复用同一校验器且 fail-close→可能降级；子层独立解析未复用→必须单独审 |
| 动态片段 | 无 | ⚠️ 直接进入结构位置 → 标记为高危，无需 barrier 验证 |
| 动态片段 | 无 | ⚠️ 直接进入结构位置 → 标记为高危，无需 barrier 验证 |

### 验证动作（强制，三选一）

对每个 barrier，必须执行以下至少一个动作：

1. **查看实现**：用 Read 工具读取 barrier 函数的实际源码，确认其行为
2. **查看调用**：确认 barrier 在调用位置被正确使用（有无遗漏参数、有无被条件分支跳过、返回值是否被使用）
3. **测试边界**：尝试构造绕过输入，验证 barrier 是否有效

### fail-close 判定标准（强制）

barrier 的稳健性必须以"失败模式"为准，不看正常路径：

- ✅ **fail-close（安全）**：未知/非法输入 → 抛异常 / 返回空 / 拒绝执行 / 日志告警，**绝不透传原始值**
- ❌ **fail-open（可绕过）**：未知/非法输入 → 默认允许 / 静默回退原始值 / 仅返回 false 但调用方未检查 → 标记为 `⚠️ 可绕过`
- ❌ **silent-fallback（高危）**：未知字段 → 透传至 SQL 拼接位置且无拦截 → 直接标记高危，无需继续 barrier 验证


### Barrier 验证输出格式

在审计报告中，每个 barrier 必须记录：

```markdown
| 参数 | Barrier 函数 | 实际行为 | 验证结果 |
|------|-------------|---------|---------|
| keyword | escape_like_literal() | 处理了 % _ [ ] 转义，Unicode 测试通过 | ✅ PASSED |
| category_id | strict_int() | 拒绝非数字输入，长度限制 10 位 | ✅ PASSED |
| sort_key | allowlisted_sort_key() | 只返回白名单字段，无 bypass | ✅ PASSED |
| column_key | 无 | 直接进入列标识符位置，无白名单 | ⚠️ FAILED |
```

### 反模式（禁止）

- ❌ 看到 `escape_like_literal()` 就判定安全 → **必须读取实现源码**
- ❌ 看到 `int.TryParse()` 就判定安全 → **必须确认返回值被正确使用**
- ❌ 看到 `switch` 就判定白名单 → **必须确认有 `default` 分支且不会 fallthrough**
- ❌ 看到参数化查询就判定安全 → **必须检查是否通过字符串插值混入**（如 `FromSqlRaw($"... {input}")`）
- ❌ 看到参数化查询就判定标识符位安全 → **参数化不保护标识符位**，`ORDER BY {param}` 仍需白名单验证

## 二阶段判定（强制）

阶段一（临时结论）：对每条命中先给出三选一临时结论
- `确认漏洞候选`：外部可控输入疑似进入 SQL 构造
- `待确认`：上下文显示可疑拼接，但外部输入来源或 barrier 行为不清晰
- `误报`：字段来自固定常量/枚举映射，或 barrier 已验证为 fail-close

阶段二（强制追证）：若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：
- ✅ 找到外部可控输入进入 SQL 位的证据 → `确认漏洞`
- ✅ 找到固定白名单映射 / fail-close 证据 → `误报`
- ❌ 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

🔴 **STOP：阶段二不允许停在表面现象，必须追证到可判定为止。**


## 判定规则（结构化）

### 确认漏洞（任一满足）

1. 外部可控参数直接进入 SQL 字符串构造（拼接 / 插值 / `StringBuilder` / `Format`）
2. 标识符位（排序字段、列名、表名、分组字段）仅做字符替换、包裹 `[]`/`"`/`` ` ``、黑名单过滤，**无白名单映射**
3. 嵌套过滤：顶层存在字段校验，但子层递归节点未执行同级校验
4. 动态片段（`where` 条件片段、`IN` 列表、`offset/fetch`、`TOP`）无白名单或 barrier 验证失败

### 待确认

1. 上下文显示可疑拼接，但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路中的参数传递未闭合

### 误报

1. 最终值或标识符来自固定常量 / 枚举映射，未知输入会拒绝（fail-close）
2. 递归所有层级均复用同一校验器并严格失败关闭
3. 参数通过 ORM 参数化绑定（非字符串插值），且标识符位有白名单保护

## 执行检查点（强制）

- EVID_SQL_EXEC_POINT
- EVID_SQL_STRING_CONSTRUCTION
- EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT

## 执行检查点

🔴 **STOP — 输出结论前必须核对以下两项，缺一不得继续：**

1. **trace-gate 检查**：若 `route_tracer/{route_id}/trace_{timestamp}.md` **不存在或 trace_status=PARTIAL/UNRESOLVED**，所有结论必须降级为 `⚠️待验证`，禁止输出 `✅已确认可利用`。
2. **EVID 完整性检查**：若 EVID_SQL_EXEC_POINT / EVID_SQL_STRING_CONSTRUCTION / EVID_SQL_USER_PARAM_TO_SQL_FRAGMENT 三者未全部满足，禁止输出高危（🔴）级别结论。

🔴 **STOP — 发现以下任意情况时，必须在输出中单独标注，不得静默略过：**

- 动态片段（排序字段/列名/表名）无白名单保护 → 单列一条 `⚠️ 白名单缺失风险`
- IgnoreQueryFilters 或 RawSQL 绕过多租户/软删除过滤器 → 单列一条 `⚠️ 过滤器绕过风险`
- 异常/日志中泄露完整 SQL 或参数值 → 单列一条 `⚠️ 信息泄露风险`

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

| # | 反模式 | 为什么错 | 正确做法 |
|---|---|---|---|
| 1 | **无 trace 时输出 ✅已确认** | 仅凭静态抓手无法证明参数可控性与执行路径 | 降级为 `⚠️待验证`，说明缺失证据 |
| 2 | **参数化查询直接判定为安全** | EF Core `FromSqlRaw($"... {userInput}")` 仍为注入风险；参数化 ≠ 无风险 | 检查参数是否通过插值混入，而非仅看调用方式 |
| 3 | **只搜一层调用，忽略封装链** | 业务层调 QueryBuilder，QueryBuilder 调 RawSQL——漏洞在最底层 | 枚举规则要求追踪到最终执行点 |
| 4 | **动态 ORDER BY/列名 当作低危忽略** | 列名/表名注入可用于 Union-based/Error-based 攻击 | 必须单独枚举不可参数化片段并给出白名单建议 |
| 5 | **把 LINQ to SQL 全部判为安全** | LINQ 可能退化为 RawSQL（含 `FromSqlRaw`、`Database.ExecuteSql` 等） | 枚举时必须检查 LINQ 表达式树的最终 SQL 形态 |
| 6 | **看到参数化查询就判定标识符位安全** | `ORDER BY {param}`、`WHERE {column} = value` 中参数化只保护值位，不保护标识符位；标识符位仍需白名单验证 | 区分"值参数化"与"标识符参数化"，标识符位必须单独验证白名单 |

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（查询入口确认）**：必须确认 SQL 执行入口与 ORM/原生调用边界。
- 🔴 **CHECKPOINT B（参数化确认）**：必须确认参数绑定而非字符串拼接。
- 🔴 **CHECKPOINT C（高危语句确认）**：必须确认动态排序、分页、批量拼接等高危片段。
- 🛑 **STOP**：若参数化证据与执行链未闭合，不得输出“无注入风险”结论。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| trace 不完整或缺失 | 回补 route_tracer 证据并对齐 route_id | 降级 `⚠️待验证`，禁止已确认可利用 |
| 参数到 SQL 片段映射不闭合 | 补齐字符串构造与执行点链路证据 | 不输出高危确认，仅给验证步骤 |
| 动态片段白名单证据不足 | 逐项核对排序/列名/表名白名单逻辑 | 保守标记高风险待验证项 |

🔴 **STOP：任一兜底触发时，禁止输出“无注入风险”。**

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如“可能有风险/建议关注/视情况而定/大概率”等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

最小输出片段（可直接复用）：

```md
- 命中ID：M{hash}（可选，用于跨阶段追踪和回归对齐）
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```

## 测试建议（强制）

对每个确认漏洞或待验证项，至少给出以下测试覆盖：

- **正向测试**：构造确认可利用的输入，验证漏洞确实存在（如 `' OR 1=1--`、`1; DROP TABLE`、非法 ORDER BY 字段）
- **负向测试**：构造被 barrier 拦截的输入，验证保护机制有效（如白名单外字段、非数字字符串、超长度输入）
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 输出

- vuln_audit/sql_{timestamp}.md
