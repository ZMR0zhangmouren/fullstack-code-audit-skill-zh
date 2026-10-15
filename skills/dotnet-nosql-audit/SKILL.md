---
name: dotnet-nosql-audit
description: .NET NoSQL 注入审计工具。识别 MongoDB、Cosmos DB 等查询构造中的结构注入、操作符注入与动态过滤风险。
---

# .NET NoSQL 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 NoSQL 查询对象、过滤器构造、聚合管道、文档更新相关的共享抓手
- 若项目存在 Repository、DocumentStore、CustomFilterBuilder、SearchGateway 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充宿主、序列化配置和运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- MongoDB Driver 中 BsonDocument、Builders.Filter、Builders.Update、Aggregation Pipeline 的动态构造路径
- JSON、Dictionary<string, object>、ExpandoObject、匿名对象或前端透传结构直接映射为查询条件的场景
- $where、$regex、$ne、$gt、$lt、$or、$expr 等操作符是否可由用户输入直接控制
- Cosmos DB、Elastic、LiteDB 或自定义文档查询语法中的字符串查询拼接与占位边界
- 排序字段、投影字段、分页条件、聚合阶段、lookup/join 子句是否使用白名单或枚举约束
- 反序列化后的对象、GraphQL 参数、Hub 消息体是否会被原样送入查询构造器
- 查询结果是否被用作认证、授权、租户边界或高价值业务判断，从而放大影响

## 枚举规则（强制细化）

- 枚举 MongoDB Driver、Cosmos DB、Elastic、LiteDB、自定义文档查询封装中的查询入口
- 优先搜索 BsonDocument、FilterDefinition、Builders.Filter、Builders.Update、Aggregate、PipelineDefinition、QueryDefinition
- 枚举来自 JSON、Dictionary、ExpandoObject、GraphQL Input、Hub 消息、动态表单的数据直接映射到查询结构的代码
- 对每个查询点记录：filter 来源、operator 是否可控、排序和投影字段是否可控、分页片段是否可控
- 单独枚举 $where、$expr、regex、script query、文本搜索和聚合 lookup / facet / union 等高危能力

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **查询结构直接映射** | 确认是否将 JSON/Dictionary/ExpandoObject/GraphQL Input 直接映射为查询结构（如 `BsonDocument.Parse(userInput)`） | 用户输入直接解析为查询结构 → 🔴 高危；有中间映射层且映射层为 fail-close → 🟠 需确认 |
| **操作符白名单** | 确认 `$where`、`$expr`、`$regex`、`$ne`、`$gt`、`$lt`、`$or` 等操作符是否可被用户输入控制 | 用户可控高危操作符 → 🔴 高危；仅允许安全操作符（如 `$eq`）且为 fail-close → ✅ 安全；白名单不可见 → ⚠️ 待确认 |
| **排序/投影字段白名单** | 确认排序字段、投影字段、分页条件是否来自白名单映射 | fail-close 白名单 → ✅ 安全；黑名单或无白名单 → 🔴 高危 |
| **聚合管道注入** | 确认 Aggregation Pipeline 中是否混入用户可控输入（如 `$lookup` 目标表、`$match` 条件） | 聚合阶段含用户可控输入 → 🔴 高危；聚合管道完全固定 → ✅ 安全 |
| **反序列化到查询结构** | 确认反序列化后的对象（如从 HTTP Body、Hub 消息）是否被原样送入查询构造器 | 原样送入且无校验 → 🔴 高危；有校验层且 fail-close → ✅ 安全 |
| **查询结果影响面** | 确认查询结果是否进入认证、授权、租户边界或高价值业务判断 | 查询结果影响认证/授权 → 🔴 高危放大；仅返回数据无后续敏感操作 → 🟠 需确认 |

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

1. 用户可控输入直接映射为查询结构（如 `BsonDocument.Parse(userInput)`），且无 barrier 验证
2. 高危操作符（`$where`、`$expr`、`$regex`）可被用户输入控制
3. 排序/投影/分页字段无白名单或白名单为 fail-open
4. 聚合管道（Aggregation Pipeline）中混入用户可控输入
5. 嵌套/递归结构（如多层 Repository 封装）中顶层存在校验，但子层未执行同级校验
6. 反序列化后的对象被原样送入查询构造器，且反序列化层无校验

### 待确认

1. 上下文显示可疑模式（如 `Builders.Filter` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如操作符白名单）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路（如消息队列消费查询请求）中的参数传递未闭合
4. JSON/Dictionary 到查询结构的映射层存在但实现不可见

### 误报

1. 最终查询结构来自固定常量 / 枚举映射，未知输入会拒绝执行（fail-close）
2. 递归所有层级均复用同一 fail-close 操作符白名单校验器
3. 用户输入仅进入安全的参数化值位（如 `$eq` 的值），且查询结构完全固定
4. 反序列化层有严格的类型校验，且校验器为 fail-close

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造 NoSQL 注入 payload（如 `{"$where": "this.password == 'admin'"}`、`{"$regex": ".*"}`、非法排序字段），验证注入确实存在
- **负向测试**：构造被 barrier 拦截的输入（如白名单外操作符、非法字段名、非预期类型），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 证据引用

- EVID_NOSQL_QUERY_CONSTRUCTION
- EVID_NOSQL_USER_INPUT_INTO_QUERY_STRUCTURE
- EVID_NOSQL_OPERATOR_INJECTION_FIELDS

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（查询结构确认）**：必须确认查询构造点与操作符使用位置。
- 🔴 **CHECKPOINT B（结构可控性确认）**：必须给出输入到查询结构/操作符的映射证据。
- 🔴 **CHECKPOINT C（影响面确认）**：必须说明查询结果是否影响认证、授权或高价值业务判断。
- 🛑 **STOP**：若仅有动态查询痕迹而无可控性映射，结论降级为 `⚠️待验证`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 动态查询存在但输入映射不完整 | 补齐输入到查询结构/操作符映射 | 降级 `⚠️待验证` |
| 操作符可控性证据不足 | 分析 `$where/$expr/regex` 等高危片段来源 | 不输出高危确认，仅给验证步骤 |
| 影响面未闭合（认证/授权/高价值业务） | 追踪查询结果在业务判断中的使用 | 保守评估风险并保留待补证 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认注入”。**

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

- 反模式：把动态查询等同注入成立。正确做法：证明用户输入进入操作符/结构。
- 反模式：忽略排序/投影字段可控性。正确做法：同时检查过滤、排序、聚合片段。
- 反模式：不区分直接依赖与传递封装。正确做法：追踪到实际 Driver 调用点。
- 反模式：证据不足仍下高危。正确做法：降级 `⚠️待验证`。

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

- vuln_audit/nosql_{timestamp}.md
- 可选：vuln_poc/nosql_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
