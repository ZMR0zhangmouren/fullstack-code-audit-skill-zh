---
name: dotnet-graphql-audit
description: .NET GraphQL 框架专项审计工具。针对 Query/Mutation/Subscription、Resolver 鉴权、输入绑定、复杂度限制与 introspection 暴露进行白盒审计。
---

# GraphQL 框架专项审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 graphql 相关的入口定义、绑定转换、前置控制、敏感操作、安全配置抓手
- 若项目存在框架二次封装、统一扩展方法、平台基座或宿主包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（如已由 `dotnet-route-mapper` 生成，用于对齐公开操作、变量绑定与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（如需对齐 Resolver 鉴权、匿名入口与资源归属边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（如需将 Resolver 与下游 SQL/SSRF/文件/模板等副作用链做交叉引用）

## 重点检查

- Resolver 级鉴权、字段级授权、schema stitching、federation、租户上下文与批量查询中的授权一致性
- Query、Mutation、Subscription 参数绑定、输入对象、别名、fragment、变量和默认值对业务校验的影响
- introspection、schema 暴露、playground、Banana Cake Pop、persisted query、复杂度限制、深度限制与批量查询边界
- 自定义 scalar、DataLoader、缓存键、批处理器、N+1 优化与越权数据复用风险
- GraphQL upload、订阅连接、WebSocket 鉴权、错误返回、调试信息和 tracing 扩展暴露
- Resolver 是否进一步调用 HttpClient.SendAsync / GetAsync、HttpWebRequest / WebRequest.Create、文件、命令、模板、数据库 RawSQL 或后台作业形成复合风险

## 枚举规则（强制细化）

- 枚举 Query、Mutation、Subscription、字段 Resolver、DataLoader、Schema 配置、授权中间件、复杂度限制器和 introspection 开关
- 优先搜索 AddGraphQL、AddQueryType、AddMutationType、AddSubscriptionType、Authorize、UsePaging、UseFiltering、UseSorting、DataLoader、UploadType、Introspection
- 枚举输入对象、变量、fragment、别名、批量查询、persisted query、上传、订阅连接和 WebSocket 握手逻辑，记录字段级校验与租户约束
- 枚举 playground、Banana Cake Pop、schema 导出、错误扩展、tracing、debug 输出和 introspection 配置，记录是否在生产环境暴露
- 对每个高风险 Resolver 记录：字段名、调用类型、授权条件、输入对象、批处理行为、下游调用类型与复合风险链路

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | Schema 操作存在且可达 | Query/Mutation/Subscription 存在且外网可达（含 playground/introspection） | BLOCKED → 无可达 GraphQL 端点，专项降为低优先级 |
| 二级 | 授权/复杂度控制存在绕过 | Resolver/字段级授权缺失，或 depth/complexity 限制可被绕过 | BLOCKED → 授权与复杂度控制完整，结论降级 |
| 三级 | 下游复合风险可达敏感操作 | Resolver 调用数据库/文件/命令/模板/SSRF 等 Sink 且未做业务鉴权 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中 GraphQL Schema/Resolver + 授权/复杂度配置 + 下游调用链，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 Query/Mutation/Subscription → Resolver → 下游调用 链路；
  2. 验证字段级授权、depth/complexity 限制与 introspection 暴露条件；
  3. 评估 Resolver 下游调用（SQL/文件/命令/模板/SSRF）的授权边界与复合风险；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：Schema 可达 + 授权/复杂度绕过 + 下游复合风险未授权。输出 `确认漏洞`。
2. **待确认**：Schema/授权/下游调用证据部分存在，但字段级授权或复杂度限制不可证实。输出 `待确认`。
3. **误报/无风险**：GraphQL 端点不可达或已保护，Resolver 均授权，复杂度限制严格，下游调用有业务鉴权。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 GraphQL 端点（Query/Mutation/Subscription）
  - 端点外网可达或 introspection/playground 在生产环境暴露
  - 或 Resolver/字段级缺少授权检查
  - 或 depth/complexity 限制可被绕过
- **测试用例建议**：
  - Happy Path：正常 GraphQL 查询经授权与复杂度限制处理，返回正确响应
  - 边界/歧义：嵌套查询深度攻击、批量查询别名绕过、introspection 敏感字段暴露、Resolver 下游 SSRF/SQL 注入
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（Schema边界确认）**：必须确认 Query/Mutation/Subscription 暴露面与鉴权边界。
- 🔴 **CHECKPOINT B（解析链确认）**：必须确认 resolver 参数来源与下游 sink 的可控链路。
- 🔴 **CHECKPOINT C（防护策略确认）**：必须确认 depth/complexity/字段级授权等防护。
- 🛑 **STOP**：若 schema 边界与解析链未闭合，不得下“风险已控”结论。

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

- 输出文件：framework_audit/graphql_{timestamp}.md
- 必须按 Schema 暴露与调试、Resolver 授权、输入与批处理、订阅与复合风险 四个章节组织结果
- 每个问题点必须写明 字段或 Resolver、调用类型、授权模型、输入对象、下游组件调用
- 必须单列 Query、Mutation、Subscription 三类面向不同攻击面的结论，避免只给笼统 GraphQL 总结

## 证据引用

- EVID_AUTH_PERMISSION_CHECK_EXEC
- EVID_SSRF_URL_NORMALIZATION
- EVID_SQL_EXEC_POINT
- EVID_XSS_OUTPUT_POINT

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| Resolver 鉴权注解存在但运行时策略不可见 | 输出注解与策略引用证据 | 标记 PARTIAL，禁止越权已确认结论 |
| 复杂度/深度限制配置缺失上下文 | 记录 schema 与中间件配置点 | 降级为待验证并列缺失项 |
| Resolver 下游调用可见但参数映射不完整 | 输出调用点与候选变量映射 | 不输出高强度利用链，转待补证 |
| introspection 暴露仅在开发配置可见 | 分环境给出配置差异 | 结论限定环境，不做泛化 |

🔴 **STOP：Resolver 授权链与下游调用链未闭合时，不得输出“确认可利用”结论。**

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
| 1 | 将 Query/Mutation/Subscription 混为一类 | 攻击面差异明显 | 分类型分别下结论 |
| 2 | 把 introspection 开启直接判高危 | 需结合鉴权与可达性 | 给出暴露条件与利用前提 |
| 3 | 只看 schema 不看 resolver 实现 | 证据不足易误判 | 必须下钻 resolver 代码 |

输出类型映射：AUTH、LOGIC、SSRF、CFG、XSS。
