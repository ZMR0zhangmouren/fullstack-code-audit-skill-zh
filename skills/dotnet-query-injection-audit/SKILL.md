---
name: dotnet-query-injection-audit
description: .NET 非 SQL 查询语言注入审计工具。识别 SOQL（Salesforce）、OData、FetchXML（Dynamics 365）查询字符串拼接、结构化 API 条件值误用与 [EnableQuery] 原始查询直通导致的注入风险，输出分级、PoC 与修复建议。
---

# .NET 非 SQL 查询语言注入审计（SOQL / OData / FetchXML）

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 的「QUERY / 非 SQL 查询语言」章作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖 QUERY 章中的入口定义：SOQL `ForceClient.QueryAsync` / `SforceService.query`、OData `$filter` / `$orderby` 拼接与 `[EnableQuery]`、FetchXML `RetrieveMultiple(QueryBase)` / `ConditionExpression`
- 若项目存在 SOQL Builder、OData Helper、FetchXML 封装器等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- **本专项为 trace-gate 类型**：`route_tracer/{route_id}/trace_{timestamp}.md` 为硬前置证据；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（用于确认匿名入口、P0/P1 分桶与查询结果的数据敏感度）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充 OData 路由约定、Salesforce / Dynamics 365 客户端配置与运行时控制面）
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致
- trace 缺失或 `trace_status=PARTIAL/UNRESOLVED` 时，所有结论降级为 `⚠️待验证`（见「二阶段判定」）

## 重点检查

- SOQL 构造点：`ForceClient.QueryAsync<T>(soql)`、`SforceService.query(soql)`、REST `/query?q=` 的查询字符串来源与拼接方式
- OData 构造点：`$filter=` / `$orderby=` / `$select=` / `$expand=` 查询选项字符串拼接；`ODataClient` / `Container` LINQ 提供者逃逸为原始查询字符串
- FetchXML 构造点：FetchXML 字符串中的 `<filter>`、`<condition` 片段直拼；`RetrieveMultiple(QueryBase)` 执行入口
- 结构化 API（QueryExpression / 强类型查询对象）的条件值可控性：`new ConditionExpression(attr, op, userInput)` 中 userInput 是否经类型/范围校验
- `[EnableQuery]` 原始查询直通：Web API OData 中客户端 `$filter` 等查询选项未经服务端约束直接下推数据源的入口
- 字符串拼接、插值字符串、StringBuilder、AppendFormat、Join 生成查询片段的路径
- 动态属性名、排序字段、过滤操作符、`<condition operator=` 操作符位等"无法参数化"的动态片段是否有 allowlist
- 多租户/行级安全过滤器是否被注入的查询片段绕过（如 OData `$filter` 追加 `or 1 eq 1`、FetchXML 注入 `or` 条件块）
- 异常处理、日志和调试输出中是否暴露完整查询字符串、查询参数和数据源 endpoint

## 枚举规则（强制细化）

- 枚举所有继承 Controller / ControllerBase、Service、Background Job、GraphQL Resolver、Hub 中的非 SQL 查询调用点
- 优先搜索：`QueryAsync`、`query(`、`RetrieveMultiple`、`ConditionExpression`、FetchXML 字符串（`<filter>`、`<condition`）、OData `$filter` / `$orderby` 拼接、`[EnableQuery]`
- 枚举字符串拼接、插值字符串、StringBuilder、AppendLine、Join、Format、SOQL Builder / FetchXML Helper 的使用位置
- 单独枚举"不可参数化片段"：动态属性名、排序字段、过滤操作符、`<condition operator=` 操作符位、`$select` / `$expand` 字段列表
- 枚举 SOQL Builder、OData Helper、FetchXML 封装器、自定义查询构造器的封装链路，追踪到最终执行点
- 对每个命中记录：文件、行号、查询语言类型（SOQL/OData/FetchXML）、构造方式（字符串拼接/结构化 API）、参数来源

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **结构化 API / 参数化** | 确认 QueryExpression、`ConditionExpression` 强类型条件值与 OData 参数化查询是否正确使用 SDK 参数绑定，而非将用户输入直接拼入查询字符串 | 条件值位全部来自强类型参数绑定且无插值混入 → ✅ 安全；调用结构化 API 但条件值仍来自字符串拼接 → ⚠️ 待确认 |
| **输入 allowlist / 类型校验** | 确认动态属性名、排序字段、过滤操作符是否来自 allowlist 映射或枚举校验，且校验为 fail-close | fail-close allowlist → ✅ 安全；黑名单或无校验 → 🔴 高危；校验实现不可见 → ⚠️ 待确认 |
| **转义** | 确认查询字符串拼接位置（SOQL 引号、OData 引号/特殊字符、FetchXML XML 实体）是否有规范转义 | 全片段规范转义且无法越界 → ✅ 安全；转义缺失或转义函数实现不可见 → ⚠️ 待确认 |
| **查询结果范围校验** | 确认注入查询片段是否可改变结果集范围（扩大返回条数、跨实体查询、绕过租户过滤），以及服务端是否对结果范围做二次校验 | 注入可扩大结果集或跨租户 → 🔴 高危；结果范围由服务端固定且注入仅影响单条条件值 → 🟠 中危待确认 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

## 二阶段判定（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

1. **阶段一（临时结论）**：对每条命中先标记 `确认漏洞候选` / `待确认` / `误报`
2. **阶段二（强制追证）**：
   - 若阶段一为 `确认漏洞候选` → 必须完成 Barrier 验证矩阵全部相关项，且 Source → 查询执行 Sink → 查询语义/影响三段证据（三个 EVID）全部引用，通过后才能标记 `已确认`
   - 若阶段一为 `待确认` → 必须向下追至少一跳调用链或下游解析器，直到可判定为止
   - 若阶段二仍无法闭合 → 保持 `待确认`，并明确记录缺失哪一跳证据
3. **trace-gate 检查**：若 `route_tracer/{route_id}/trace_{timestamp}.md` 不存在或 `trace_status=PARTIAL/UNRESOLVED`，所有结论必须降级为 `⚠️待验证`，禁止输出 `✅已确认可利用`

🔴 **STOP — 仅发现查询拼接语法、未证明用户输入进入可执行查询结构时，禁止输出「确认漏洞」，结论一律落 `⚠️待验证`，并写明缺失证据与补证动作。**

## 判定规则（强制细化）

### 确认漏洞

必须同时满足以下三项，且三个 EVID 同时引用、缺一不可：

1. **Source 闭合**：用户可控输入来源明确（`EVID_QUERY_USER_PARAM_TO_FRAGMENT`——用户输入到查询片段、条件或结构映射证据）
2. **查询执行 Sink 闭合**：输入到达 SOQL / OData / FetchXML 执行点（`EVID_QUERY_EXEC_POINT`——非 SQL 查询执行点证据）
3. **查询构造与语义影响闭合**：输入参与查询字符串/结构构造（`EVID_QUERY_STRING_CONSTRUCTION`），且注入片段改变查询语义（结果集扩大、跨实体/跨租户访问、绕过过滤）

🔴 **确认阈值（硬性规则）：未同时引用 EVID_QUERY_EXEC_POINT + EVID_QUERY_STRING_CONSTRUCTION + EVID_QUERY_USER_PARAM_TO_FRAGMENT 三者，不得输出「已确认」或 🔴/🟠 级别结论。**

### 待确认

1. 仅发现查询拼接语法（如 `$"SELECT Id FROM Account WHERE Name = '{userInput}'"`），但未证明用户输入进入可执行查询结构 → `⚠️待验证`，不得确认
2. 上下文显示可疑模式（如 `RetrieveMultiple` 调用），但外部输入来源不清晰（需补 trace 或调用链）
3. Barrier 函数（如查询参数化封装）存在，但当前分支是否调用、返回值是否被使用无法确认
4. 异步 / 队列 / 事件链路中的查询参数传递未闭合
5. 结构化 API 与字符串拼接混用，但当前调用点无法确认具体使用路径

### 误报

1. QueryExpression 强类型条件值经类型校验/枚举校验，未知输入拒绝执行（fail-close）
2. 最终查询来自固定常量 / 模板映射，未知输入会拒绝执行（fail-close）
3. 用户输入仅进入 SDK 参数化值位，查询字符串模板完全固定且无插值
4. 动态属性名/排序字段在查询构造前锁定于 fail-close allowlist，不可被覆盖
5. `[EnableQuery]` 入口的服务端约束（`AllowedQueryOptions`、`MaxTop`、行级过滤）在查询下推前强制生效，客户端查询选项不可绕过

### 反例黑名单

| # | 反模式 | 为什么错 | 正确做法 |
|---|---|---|---|
| 1 | 无 trace 时输出 ✅已确认 | 仅凭静态抓手无法证明参数可控性与执行路径 | 降级为 `⚠️待验证`，说明缺失证据 |
| 2 | 发现 `$"WHERE Name = '{input}'"` 拼接即确认高危 | 拼接语法 ≠ 用户输入进入可执行结构；常量拼接或不可达路径不构成漏洞 | 必须闭合 Source 与执行 Sink 两段证据后再确认 |
| 3 | `RetrieveMultiple(QueryExpression)` 一律判安全 | `new ConditionExpression(attr, op, userInput)` 条件值可控时同样可注入查询语义 | 检查条件值来源与类型校验，而非仅看 API 名称 |
| 4 | `[EnableQuery]` 视为 OData 天然安全 | 原始查询选项直通可让客户端任意过滤/排序/展开，扩大数据暴露面 | 核对 `AllowedQueryOptions`、行级过滤与结果范围校验 |
| 5 | 忽略 FetchXML 的 XML 注入 | `<condition value='{input}'>` 中引号逃逸可注入额外 `<condition>` 或 `or` 条件块 | 枚举 FetchXML 字符串拼接并核对 XML 转义 |

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造注入查询片段改变结果集（SOQL：`x' OR Name != NULL`（SOQL 不支持 `--` 注释，闭合引号即截断原条件）；OData：`$filter=Name eq 'x' or 1 eq 1`；FetchXML：引号逃逸拼接注入额外条件块），验证注入确实存在且结果集被扩大
- **负向测试**：构造被 barrier 拦截的输入（allowlist 外属性名/排序字段、非法类型条件值、非参数化值位），验证参数化/结构化 API 构造不受影响
- **回归测试**：修复后复测 QueryExpression 条件值校验与参数化路径，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 证据引用

- EVID_QUERY_EXEC_POINT
- EVID_QUERY_STRING_CONSTRUCTION
- EVID_QUERY_USER_PARAM_TO_FRAGMENT

## 输出

- vuln_audit/query_{timestamp}.md（漏洞编号格式：`{等级前缀}-QUERY-{序号}`，如 `H-QUERY-001`，与 shared/SEVERITY_RATING.md 类型码 QUERY 对齐）
- vuln_poc/query_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC，参考 shared/DOTNET_VULN_POC_TEMPLATE.md）
- 输出中每个命中必须记录：查询语言类型（SOQL/OData/FetchXML）、构造方式（字符串拼接/结构化 API）、trace_id 与三个 EVID 的引用状态
