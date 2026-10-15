# 输入/输出路径约定（.NET 全 Skill 统一）

本文件消除“逻辑章节名”和“物理落盘路径”之间的歧义，dotnet-* Skill 与 dotnet-audit-pipeline 全部适用。

## 两种执行形态

| 形态 | 含义 |
| ---- | ---- |
| 流水线合并 | 由 dotnet-audit-pipeline 编排时，最终会形成一份总报告，但默认仍要求先真实创建各阶段结构化产物目录与文件 |
| 单 Skill 独立跑 | 仅调用某个 Skill 时，可按建议路径真实创建目录与文件 |

## 默认执行模式（强制落盘）

dotnet-security-audit-skill 默认采用 强制落盘 模式，而不是仅保留逻辑章节。

默认情况下，执行 dotnet-audit-pipeline 后应至少真实创建以下目录：

- codegraph/
- scan_audit/
- coverage_audit/
- design_intent/                # 设计意图摘要（阶段 0.7 产物，无结果也需建目录写状态）
- route_mapping/
- auth_audit/
- route_tracer/
- briefing/
- vuln_audit/
- vuln_poc/
- framework_audit/
- cross_analysis/
- vuln_report/
- exploit_chain/
- global_sink_fallback/
- review/
- quality/

如果某一阶段没有产出可确认内容，也应创建对应目录，并在该目录的索引文件或阶段文件中写明“无结果 / 未执行 / 待验证 / 环境依赖”的原因，而不是直接缺目录。

## 阶段索引文件与空结果文件（强制）

每个阶段目录默认应至少包含一份索引文件，用于记录：

- 本阶段调用了哪些 Skill
- 实际生成了哪些文件
- 哪些结果为空
- 哪些结果仅为初筛或部分完成

推荐的阶段索引文件：

- scan_audit/index_{timestamp}.md
- coverage_audit/index_{timestamp}.md
- route_mapping/index_{timestamp}.md
- auth_audit/index_{timestamp}.md
- route_tracer/index_{timestamp}.md
- briefing/index_{timestamp}.md
- vuln_audit/index_{timestamp}.md
- vuln_poc/index_{timestamp}.md
- framework_audit/index_{timestamp}.md
- cross_analysis/index_{timestamp}.md
- review/index_{timestamp}.md
- vuln_report/index_{timestamp}.md
- quality/pipeline_execution_{timestamp}.md
- quality/api_coverage_gate_{timestamp}.md
- quality/quick_validation_{timestamp}.md（建议，交付前快速收尾校验）
- quality/quick_validation_example_{timestamp}.md（建议，培训/回归对照示例）
- quality/coverage_consistency_check_{timestamp}.md（建议，跨产物字段一致性核对）
- quality/final_anchor_checklist_{timestamp}.md（建议，收尾锚点逐文件勾选与汇总）

如果某目录下无明确结果，也必须至少创建以下两者之一：

- index_{timestamp}.md：记录“无结果 / 未执行 / 待验证 / 环境依赖 / 初步筛选”的状态
- empty_result_{timestamp}.md：用于说明该阶段为何没有形成正式发现或正式文件

不允许目录存在但没有索引说明文件。

## 漏洞专项状态模型（强制）

dotnet-*-audit 在执行过程中，至少应使用以下状态之一：

| 状态 | 含义 |
| ---- | ---- |
| NOT_RUN | 未执行；必须说明原因 |
| INITIAL_SCREENED | 已做初步筛选；仅进行了基础枚举或粗筛，尚未完成证据闭合 |
| PARTIAL | 部分完成；已进入专项分析，但 trace、框架前提或环境证据未完全闭合 |
| COMPLETED | 已完成；具备当前阶段要求的专项结论输出 |
| NOT_APPLICABLE | 不适用；必须说明为何该项目或该入口不适用 |

约束：

- 非重点漏洞类型在一次默认执行中，允许停留在 INITIAL_SCREENED 或 PARTIAL，但不能完全没有记录
- 即使没有发现问题，也必须记录 skill 已执行且结果为 NO_ISSUE 或 NO_FINDING
- 最终 report 必须可回溯每个 dotnet-*-audit skill 的执行状态与是否发现问题
- 漏洞 index（`vuln_audit/index_{timestamp}.md`）必须含「## 专项派发核对」节：`PHASE_STATUS` 全部 ACTIVE 专项逐一对勾，三态之一——`触发`（附产物路径）/ `否定证据`（NOT_APPLICABLE，含范围 + rg 模式）/ `不适用`（附理由）；禁止裸「未触发」「未执行」字样，缺行即静默漏派发。
- 漏洞 index 必须同时含「## 维度核对」节（与「专项派发核对」并列，2026-09-20 起）：台账登记的全部机制扩展维度逐条三态对勾——`覆盖`（附产物节位置）/ `否定证据`（含范围 + rg 模式）/ `不适用`（附判定理由）；禁止裸「未覆盖」「未提及」字样，缺行即维度静默缺失。维度真源双轨：登记真源=台账（`docs/新增Skill登记.md` 第二节各机制扩展条目的「覆盖机制」字段），执行真源=本附录维度清单快照（「维度清单（执行真源快照，2026-09-21）」）；新维度必须先登记（CLAUDE.md 第 0 条「先登记后实施」）并同步本快照，再入专项强制枚举清单，禁止专项正文自增未登记维度。维度否定证据纪律同专项派发核对（范围 + rg 模式，非空泛断言）。

## 规范名与常见物理路径

| 规范名 | 常见物理路径 | 说明 |
| ---- | ---- | ---- |
| codegraph_index_status_{timestamp}.md | codegraph/codegraph_index_status_{timestamp}.md | CodeGraph 索引状态与元数据 |
| codegraph_index_validation_{timestamp}.md | quality/codegraph_index_validation_{timestamp}.md | CodeGraph 索引质量校验结果 |
| scan_{filename}_{timestamp}.md | scan_audit/scan_{filename}_{timestamp}.md | 单文件安全扫描报告（阶段 0.5，FULL/SAMPLE 逐文件） |
| scan_{module}_{timestamp}.md | scan_audit/scan_{module}_{timestamp}.md | 按模块聚合的扫描报告（INCREMENTAL 模式） |
| scan_audit/index_{timestamp}.md | scan_audit/index_{timestamp}.md | 扫描批次总索引 |
| coverage_{filename}_{timestamp}.md | coverage_audit/coverage_{filename}_{timestamp}.md | 单文件覆盖补检报告（阶段 0.6） |
| backfill_{round}_{filename}_{timestamp}.md | coverage_audit/backfill_{round}_{filename}_{timestamp}.md | 覆盖补检轮次记录 |
| coverage_audit/index_{timestamp}.md | coverage_audit/index_{timestamp}.md | 覆盖批次总索引 |
| controller_inventory_{timestamp}.md | route_mapping/controller_inventory_{timestamp}.md | 控制器与 action 对账清单 |
| routes_{timestamp}.md | route_mapping/routes_{timestamp}.md | HTTP / Hub / GraphQL / WCF 入口清单 |
| params_{timestamp}.md | route_mapping/params_{timestamp}.md | 与入口逐条对应的参数结构 |
| auth_mapping_{timestamp}.md | auth_audit/auth_mapping_{timestamp}.md | 鉴权静态分桶 |
| high_risk_routes_{timestamp}.md | cross_analysis/high_risk_routes_{timestamp}.md | 高危入口集合 |
| sampled_high_risk_routes_{timestamp}.md | cross_analysis/sampled_high_risk_routes_{timestamp}.md | 样本模式下的高危候选入口集合（非全量） |
| trace_batch_plan_{timestamp}.md | cross_analysis/trace_batch_plan_{timestamp}.md | 分批追踪计划 |
| sink_suspect_dict_{timestamp}.md | cross_analysis/sink_suspect_dict_{timestamp}.md | 项目私有 SINK_SUSPECT 参数名词典（拼音/缩写/DTO 深层字段/业务术语，阶段 1 参数枚举后生成） |
| briefing_{sink_id}_{timestamp}.md | briefing/briefing_{sink_id}_{timestamp}.md | 单 sink 候选参数清单（阶段 3.5） |
| briefing/index_{timestamp}.md | briefing/index_{timestamp}.md | 候选参数清单批次总索引 |
| review_{sink_id}_{round}_{timestamp}.md | review/review_{sink_id}_{round}_{timestamp}.md | 单 sink 单轮证据质检结果（阶段 4.5）；Schema 含 `evidence_spotcheck_count` / `evidence_spotcheck_failures` 字段，REJECT 可标注 `evidence_fabrication_suspected` |
| review/index_{timestamp}.md | review/index_{timestamp}.md | 质检批次总索引 |
| route_tracer/{route_id}/... | route_tracer/{route_id}/... | 追踪分桶产物 |
| vuln_audit/{type}_{timestamp}.md | vuln_audit/{type}_{timestamp}.md | 漏洞专项产物 |
| vuln_audit/query_{timestamp}.md | vuln_audit/query_{timestamp}.md | 非 SQL 查询注入专项产物 |
| vuln_audit/export_{timestamp}.md | vuln_audit/export_{timestamp}.md | 电子表格公式注入专项产物 |
| vuln_audit/prompt_{timestamp}.md | vuln_audit/prompt_{timestamp}.md | AI 提示注入专项产物 |
| vuln_poc/{type}_{timestamp}.md | vuln_poc/{type}_{timestamp}.md | 漏洞专项 PoC / 待验证 PoC 产物 |
| framework_audit/{name}_{timestamp}.md | framework_audit/{name}_{timestamp}.md | 框架专项产物 |
| exploit_chains_{timestamp}.md | exploit_chain/exploit_chains_{timestamp}.md | 利用链聚合报告（含覆盖口径与 consistency_check_status） |
| vuln_report/{project_name}_nuget_vuln_report_{timestamp}.md | vuln_report/{project_name}_nuget_vuln_report_{timestamp}.md | 依赖漏洞报告（产物头部字段含 `knowledge_cutoff_date` / `offline_report_source`，2026-09-18 起） |
| index_{timestamp}.md | {stage}/index_{timestamp}.md | 阶段索引文件，记录本阶段执行状态与产物清单 |
| empty_result_{timestamp}.md | {stage}/empty_result_{timestamp}.md | 空结果说明文件，记录无结果原因 |
| pipeline_execution_{timestamp}.md | quality/pipeline_execution_{timestamp}.md | 总执行清单与 Skill 使用跟踪 |
| manifest_{run_id}.md | quality/manifest_{run_id}.md | 断点续跑 manifest（阶段状态机、trace_status、execution_status、中断点与下一步动作；强制） |
| preflight_{timestamp}.md | quality/preflight_{timestamp}.md | 阶段 0 preflight 环境核查（模型枚举探测 / `.codegraph` 向上解析 / dotnet SDK 可用性 / 凭证可用性声明；降级项进 manifest `gate_reason`，2026-09-20 起） |
| incremental_scope_{timestamp}.md | quality/incremental_scope_{timestamp}.md | INCREMENTAL 模式变更范围说明（变更基线、变更文件集、受影响调用链扩展说明） |
| api_coverage_gate_{timestamp}.md | quality/api_coverage_gate_{timestamp}.md | API 覆盖门禁结果（覆盖率与未映射清单） |
| unmapped_routes_{timestamp}.md | quality/unmapped_routes_{timestamp}.md | 未映射入口清单与下一轮补图建议（PARTIAL 时强制） |
| route_mapping_backfill_loop_{timestamp}.md | quality/route_mapping_backfill_loop_{timestamp}.md | 循环补图轮次记录（建议） |
| quick_validation_{timestamp}.md | quality/quick_validation_{timestamp}.md | 收尾校验结果（状态一致性与声明完整性） |
| quick_validation_example_{timestamp}.md | quality/quick_validation_example_{timestamp}.md | 收尾校验最小示例（培训/回归参考） |
| coverage_consistency_check_{timestamp}.md | quality/coverage_consistency_check_{timestamp}.md | 跨产物字段一致性核对（gate/trace/exploit-chain/final report） |
| final_anchor_checklist_{timestamp}.md | quality/final_anchor_checklist_{timestamp}.md | 收尾锚点逐文件勾选清单（含 PASS/BLOCKED/PENDING 汇总） |
| DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md | skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md | 最终报告质量章节固定模板（单一真源） |

## design_intent search_scope 与意图源（2026-09-18）

- 探测目录模式（后缀匹配，递归任意深度，排除 node_modules/bin/obj/dist/build/.next/.nuxt/coverage/.git）：
  `**/docs/superpowers/specs/*.md`、`**/docs/superpowers/plans/*.md`、`**/docs/design/*.md`、`**/.superpowers/sdd/*/`、`**/docs/adrs/*.md`（白名单默认启用）、`**/docs/rfcs/*.md`（白名单默认启用）
- 产物「采集状态」节必须含 `search_scope` 块（格式见 spec §2.3 代码块）
- 否定结论复核协议见 `AUDIT_EXECUTION_COMMON.md` §9 规则⑤

## 最终报告固定字段回写来源（建议）

当最终报告复用 `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md` 时，以下字段应与对应产物保持一一映射：

| 最终报告字段 | 推荐来源文件 | 回写要求 |
| ---- | ---- | ---- |
| `consistency_check_source` | `quality/coverage_consistency_check_{timestamp}.md` | 若该文件存在，路径应原样回写 |
| `consistency_check_status` | `quality/coverage_consistency_check_{timestamp}.md` | 与 `final_status` 保持一致 |
| `exploit_chain_consistency_check_counts` | `exploit_chain/exploit_chains_{timestamp}.md` | 与 exploit_chain 总览表统计一致 |
| `final_anchor_checklist_source` | `quality/final_anchor_checklist_{timestamp}.md` | 若该文件存在，路径应原样回写 |
| `final_anchor_decision` | `quality/final_anchor_checklist_{timestamp}.md` | 与 checklist 汇总区块中的 `final_anchor_decision` 保持一致 |
| `final_anchor_checklist_counts` | `quality/final_anchor_checklist_{timestamp}.md` | 与 `checklist_pass_count / checklist_blocked_count / checklist_pending_count` 保持一致 |

补充约束：

- 若存在 `quality/final_anchor_checklist_{timestamp}.md`，最终报告不得省略 `4.6) 收尾锚点检查结果引用`
- 若 `final_anchor_decision = BLOCKED`，最终报告不得使用“可交付”“收尾完成”“最终通过”等正向收尾措辞
- 若 `api_coverage_status = PARTIAL`，应同时存在 `quality/unmapped_routes_{timestamp}.md`，并建议在 final anchor 或最终报告说明中保留其阻断关系

### 收尾字段对账静态映射模板（P3）

| 字段 | 单一真源 | 消费方 | 对账规则 |
| ---- | ---- | ---- | ---- |
| api_coverage_status | quality/api_coverage_gate_*.md | 最终报告 2) 覆盖门禁摘要、manifest | gate 值 = 报告值，不一致 FAIL |
| pipeline_execution | quality/pipeline_execution_*.md | manifest、quick_validation | COMPLETED 时 gate 须 COMPLETE 且 percent=100%（FULL） |
| dotnet_api_coverage_status 等四声明 | 各栈 gate + cross/contract gate | 全栈最终报告 | 字段可回溯（validate_audit.py 检查 F） |
| contract_coverage_percent | cross/contract_coverage_gate_*.md | 全栈报告 2.1) | = matched/(matched+frontend_only+backend_only) |
| final_anchor_decision | quality/final_anchor_checklist_*.md | 最终报告 4.6 | PASS/BLOCKED/PENDING 与汇总计数逐字段对齐 |

- final_anchor 机器校验三行（池计数=唯一 id 数/统计表=详情枚举数/链状态分解）结果须入 checklist 汇总区块

## final_anchor ↔ final_report 4.6 最小对账示例

用途：帮助执行人快速核对"收尾锚点清单汇总区块"与"最终报告 4.6 字段"是否对齐，防止一处改了另一处漏改。

### checklist 汇总区块（quality/final_anchor_checklist_{timestamp}.md）

```
## 汇总
- checklist_pass_count: 3
- checklist_blocked_count: 2
- checklist_pending_count: 0
- final_anchor_decision: BLOCKED
```

### 最终报告 4.6 回写字段（必须与上方一一对应）

```
### 4.6) 收尾锚点检查结果引用（建议）
- final_anchor_checklist_source: quality/final_anchor_checklist_{timestamp}.md
- final_anchor_decision: BLOCKED
- final_anchor_checklist_counts: {PASS:3, BLOCKED:2, PENDING:0}
```

对账时三个字段的映射关系：

| 最终报告字段 | 对应 checklist 字段 | 对账规则 |
| ---- | ---- | ---- |
| `final_anchor_decision` | `final_anchor_decision` | 值必须完全一致 |
| `final_anchor_checklist_counts.PASS` | `checklist_pass_count` | 数值必须一致 |
| `final_anchor_checklist_counts.BLOCKED` | `checklist_blocked_count` | 数值必须一致 |
| `final_anchor_checklist_counts.PENDING` | `checklist_pending_count` | 数值必须一致 |

对账失败的典型错误（不得出现）：

- checklist 写 `final_anchor_decision: BLOCKED`，final_report 写 `final_anchor_decision: PASS`
- checklist 写 `checklist_blocked_count: 2`，final_report 写 `{PASS:5, BLOCKED:0, PENDING:0}`
- final_report 写了 `4.6` 但 `final_anchor_checklist_source` 为空
## 读取规则

当某 Skill 写“读取 route_mapping/routes_*.md”时，在合并模式下应理解为“读取汇总报告中与 routes_{timestamp}.md 等价的路由章节”。

但 dotnet-security-audit-skill 的默认执行模型仍要求先真实创建物理产物，再由 pipeline 汇总，因此汇总报告不应替代原始阶段文件。

最终 report 中的执行矩阵必须能反向映射到各阶段目录下的 index_{timestamp}.md 或 empty_result_{timestamp}.md。

## 覆盖门禁与完成态约定（强制）

- `coverage_mode` 允许 `FULL | SAMPLE | INCREMENTAL`，默认 `FULL`
- `coverage_mode = INCREMENTAL` 时：必须落盘 `quality/incremental_scope_{timestamp}.md`；当变更集合（含扩展调用链）内 100% 覆盖时允许 `pipeline_execution=COMPLETED`，但最终报告必须声明 `coverage_mode=INCREMENTAL`、变更基线（commit 范围）、受影响文件数/总文件数，禁止“全量审计完成”措辞
- 只有在 `api_coverage_status = COMPLETE` 时，才允许输出正式 `cross_analysis/high_risk_routes_{timestamp}.md`
- 若 `api_coverage_status = PARTIAL` 或 `coverage_mode = SAMPLE`，必须输出 `cross_analysis/sampled_high_risk_routes_{timestamp}.md`
- 若 `api_coverage_status = PARTIAL`，必须输出 `quality/unmapped_routes_{timestamp}.md`
- 若 `api_coverage_status = PARTIAL` 且未获用户显式终止，不得结束 route mapping 循环补图
- 当 `api_coverage_status != COMPLETE` 时，`quality/pipeline_execution_{timestamp}.md` 中的 `pipeline_execution` 不得标记为 `COMPLETED`
- 若存在 `quality/final_anchor_checklist_{timestamp}.md`，最终报告中的 `final_anchor_checklist_source`、`final_anchor_decision`、`final_anchor_checklist_counts` 必须与该文件一致
- 若 `final_anchor_decision = BLOCKED`，最终报告不得写为“交付通过”或等价正向完成结论
- 最终报告必须同时声明 `audit_surface_status` 与 `api_coverage_status`，不得用单一“已完成”替代
- `cross_analysis/trace_batch_plan_{timestamp}.md` 必须满足覆盖模式阈值：
	- FULL：`trace_batch_max_size` 在 10–30
	- SAMPLE：`trace_batch_max_size` 在 5–10，且不得超过 10
	- SAMPLE：`planned_batch_count <= batch_count_upper_bound(=6)`，超限必须回退重排
- 若存在 `quality/coverage_consistency_check_{timestamp}.md` 且 `final_status=BLOCKED`：
	- `exploit_chain/exploit_chains_{timestamp}.md` 的链路可行性不得标记“确认可行”
	- 最终报告中的 `exploit_chain_consistency_check_counts` 必须反映 BLOCKED 数量

## 路由计数双字段口径（强制）

- `unique_path_count`：去重后的唯一路径数。
- `method_path_count`：(method, path) 展开总数；**跨端契约对账的唯一消费口径**。
- 两字段必须同时在 routes 文件头部、controller_inventory / route_module_inventory、api_coverage_gate 中写出；只写一个、或两值矛盾，即口径违规（validate_audit.py  WARN 兜底）。
- 历史产物若无双字段不追责；新产物必须双字段齐备。

## PoC 占位符规则

- 真实路由与参数必须替换进请求模板
- 允许保留的会话占位符：{host}、{cookie}、{token}、{apiKey}、{jwt}
- 当条件不足以构造完整可复现请求时，也应在 vuln_poc/{type}_{timestamp}.md 中输出待验证或环境依赖的 PoC 模板，不得因无法完全复现而省略该目录

## Node.js 与跨端产物路径（全栈扩展）

| 规范名 | 物理路径 | 说明 |
| ---- | ---- | ---- |
| stack_detect_{timestamp}.md | node/stack_detect/stack_detect_{timestamp}.md | 阶段0 node 技术栈检出（产物要点含内嵌异栈项目归属决策表（2026-09-18 起）） |
| route_module_inventory_{timestamp}.md | node/route_mapping/route_module_inventory_{timestamp}.md | 路由模块对账清单（镜像 controller_inventory） |
| routes_{timestamp}.md | node/route_mapping/routes_{timestamp}.md | node 入口清单 |
| frontend_outbound_{timestamp}.md | node/route_mapping/frontend_outbound_{timestamp}.md | 前端出站端点采集产物（node-route-mapper；结构含自备「## 方法不确定清单」节，2026-09-21 起） |
| params_{timestamp}.md | node/route_mapping/params_{timestamp}.md | 参数结构 |
| middleware_inventory_{timestamp}.md | node/route_mapping/middleware_inventory_{timestamp}.md | 中间件清单（鉴权面） |
| route_mapping_index_{timestamp}.md | node/route_mapping/index_{timestamp}.md | node 路由映射阶段索引 |
| feature_api_map_{timestamp}.md | node/route_mapping/feature_api_map_{timestamp}.md | 功能↔API 三层映射（node-feature-api-mapper；视图层参考，禁止作 EVID 证据源；PARTIAL 时伴随 unmapped_feature_calls_{timestamp}.md） |
| auth_mapping_{timestamp}.md | node/auth_audit/auth_mapping_{timestamp}.md | 鉴权静态分桶 |
| trace_{timestamp}.md | node/route_tracer/{route_id}/trace_{timestamp}.md | 单路由追踪 |
| trace_summary_{timestamp}.md | node/route_tracer/{route_id}/trace_summary_{timestamp}.md | 单路由追踪汇总 |
| high_risk_routes_{timestamp}.md | node/cross_analysis/high_risk_routes_{timestamp}.md | 高危入口集合 |
| trace_batch_plan_{timestamp}.md | node/cross_analysis/trace_batch_plan_{timestamp}.md | 分批追踪计划 |
| global_sink_fallback_dir | node/global_sink_fallback/ | 全局 sink 兜底目录 |
| npm_audit_{timestamp}.md | node/vuln_scanner/npm_audit_{timestamp}.md | 依赖漏洞扫描（产物头部字段含 `knowledge_cutoff_date` / `offline_report_source`，2026-09-18 起） |
| vuln_audit_{type}_{timestamp}.md | node/vuln_audit/{type}_{timestamp}.md | 漏洞专项产物 |
| vuln_audit_export_{timestamp}.md | node/vuln_audit/export_{timestamp}.md | 电子表格公式注入专项产物 |
| vuln_audit_prompt_{timestamp}.md | node/vuln_audit/prompt_{timestamp}.md | AI 提示注入专项产物 |
| vuln_poc_{type}_{timestamp}.md | node/vuln_poc/{type}_{timestamp}.md | 漏洞专项 PoC |
| framework_audit_{name}_{timestamp}.md | node/framework_audit/{name}_{timestamp}.md | P2 框架专项 |
| exploit_chains_{timestamp}.md | node/exploit_chain/exploit_chains_{timestamp}.md | 利用链聚合（ACTIVE，node-exploit-chain-audit） |
| codegraph_index_{timestamp}.md | node/codegraph/codegraph_index_{timestamp}.md | node CodeGraph 索引本体（ACTIVE；无环境记 NOT_RUN） |
| codegraph_index_status_{timestamp}.md | node/codegraph/codegraph_index_status_{timestamp}.md | node CodeGraph 索引状态与元数据 |
| scan_{filename|module}_{timestamp}.md | node/scan_audit/scan_{filename|module}_{timestamp}.md | 阶段 0.5 风险扫描（risks + safe_regions，只发现不判定） |
| coverage_{filename|module}_{timestamp}.md | node/coverage_audit/coverage_{filename|module}_{timestamp}.md | 阶段 0.6 覆盖补检（gap 计算与补检记录） |
| briefing_{sink_id}_{timestamp}.md | node/briefing/briefing_{sink_id}_{timestamp}.md | 阶段 3.5 候选参数清单（sink 参数 checklist） |
| cross_stack_exploit_chains_{timestamp}.md | cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md | 跨端利用链（stack_mode=BOTH；taint-linker XTRACE 聚合，落 {output_root}/cross/） |
| vuln_report_index_{timestamp}.md | node/vuln_report/index_{timestamp}.md | 漏洞报告索引 |
| api_coverage_gate_{timestamp}.md | node/quality/api_coverage_gate_{timestamp}.md | API 覆盖门禁 |
| unmapped_routes_{timestamp}.md | node/quality/unmapped_routes_{timestamp}.md | 未映射入口清单 |
| manifest_{run_id}.md | node/quality/manifest_{run_id}.md | 断点续跑 manifest |
| preflight_{timestamp}.md | node/quality/preflight_{timestamp}.md | 阶段 0 preflight 环境核查（模型枚举探测 / `.codegraph` 向上解析 / node 运行时可用性 / 凭证可用性声明；降级项进 manifest `gate_reason`，2026-09-20 起） |
| cross_api_contract_map_{timestamp}.md | cross/api_contract_map_{timestamp}.md | 前后端契约对账（三桶） |
| cross_contract_coverage_gate_{timestamp}.md | cross/contract_coverage_gate_{timestamp}.md | 契约覆盖门禁 |
| cross_taint_links_{timestamp}.md | cross/cross_taint_links_{timestamp}.md | P2 跨端污点链 |
| cross_consistency_findings_{timestamp}.md | cross/consistency_findings_{timestamp}.md | P2 两侧一致性 |

规则：

- node 子树完整镜像 dotnet 侧“强制落盘/阶段索引/空结果说明”约定；某一阶段没有产出时也应创建对应目录与索引说明文件。
- **全栈统一 `run_timestamp`（2026-09-20，强制）**：fullstack 编排执行时，本文档及各子栈规范名中的 `{timestamp}` 一律取全栈编排层生成并下发双栈的 `run_timestamp`（格式 `YYYY_MM_DD_HH_mm`），双栈全部产物命名（含 `{output_root}/dotnet/` 与 `{output_root}/node/` 子树及全栈级 quality/、cross/ 产物）必须用之，禁止双栈各自独立生成时间戳；子栈实际启动时刻与 `run_timestamp` 的差异只在各自 `quality/manifest_*.md` 的映射表中登记体现，不得以子栈自产时间戳命名产物。
- **preflight 命名衔接（2026-09-20）**：上条 `run_timestamp` 条款同样适用于 `preflight_{timestamp}.md`——fullstack 编排下其 `{timestamp}` 一律取 `run_timestamp`，禁止子栈自产时间戳命名。
- `api_coverage_status=PARTIAL` 时必须落盘 `node/quality/unmapped_routes_{timestamp}.md`，并继续 route mapping 补图循环，除非用户显式接受 PARTIAL 并终止。
- 跨端利用链 `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` 为全栈级正式产物（stack_mode=BOTH）：由 cross-stack-taint-linker 的 XTRACE 链聚合产出，落 `{output_root}/cross/`；无跨端链时以 `empty_result_{timestamp}.md` 记录 NOT_APPLICABLE；`consistency_check_status=BLOCKED` 时其可行性判定同样遵守降级语义，`audit_surface_status=COMPLETED` 以该产物已生成为前置条件。

### 待补证风险池单一真源（2026-09-18）

- 各产物末尾「## 本文件待补证池」节，行格式：`| pool_id | 来源产物 | 来源栈 | 关联链/发现 | 缺失证据 | 补证动作 | 责任交接 |`；pool_id 规则 `PEND-{栈}-{序号}`（如 `PEND-DOTNET-003`），真源内全局唯一
- 单一真源：`quality/pending_pool_{timestamp}.md`（fullstack 为 `{output_root}/quality/`，单栈同），收尾双保险自动聚合生成，文件头必含 `pool_total: {N}`、聚合时间、来源产物清单
- 最终报告风险池节与 `audit_surface_status` 降级依据只消费 pending_pool 计数与路径
- 行格式扩展第八字段「闭合方式」（2026-09-19）：`| pool_id | 来源产物 | 来源栈 | 关联链/发现 | 缺失证据 | 补证动作 | 责任交接 | 闭合方式 |`
- 闭合方式三枚举：`static-evidence`（纯静态可闭合）/ `dynamic-unit`（阶段 7 DYNAMIC_VERIFY(STATIC_UNIT) 可执行）/ `needs-env`（需运行环境，集成级另立项）
- 条目状态枚举：`OPEN` / `DYNAMIC_VERIFIED` / `CLOSED`（2026-09-21 起；`CLOSED` = 静态/阶段内闭合——证据链在静态审计或本执行阶段内已闭合，无需进入待补证等待流程，闭合方式仍按三枚举登记）；聚合按状态分桶计数（`open_count` / `dynamic_verified_count` / `closed_count`），`pool_total` 口径不变；原编排层自扩 `closed_in_phase6_count` 字段废止，统一归并 `closed_count` 口径（历史产物出现该字段时聚合按 `closed_count` 对待并注明）
- 历史产物无闭合方式字段：聚合时按补证动作文本启发式推断（含「动态验证/单测/复现」→dynamic-unit；含「租户/凭证/环境/运行实例」→needs-env；其余→static-evidence），并在聚合文件注明推断条数
- 动态验证报告登记（2026-09-19）：`quality/dynamic_verify_report_{timestamp}.md`（阶段 7 DYNAMIC_VERIFY(STATIC_UNIT) 产物；fullstack 为 `{output_root}/quality/`，单栈同；node 镜像 `node/quality/dynamic_verify_report_{timestamp}.md`）
- 动态验证临时工程目录登记（2026-09-19）：`quality/dynamic_verify_scratch/`（全仓唯一允许写入的临时测试工程目录，逐案例 `case_{pool_id}/` + `run_{pool_id}.log`；node 镜像 `node/quality/dynamic_verify_scratch/`）
- **一 id 一行（2026-09-20，强制）**：「## 本文件待补证池」节与 `pending_pool_{timestamp}.md` 聚合文件均为**一 id 一行**，禁止别名合并（同一 pool_id 以多个别名/变体写在同一行）。一条待补证关联多个目标（多个链/多个发现/多文件证据）时：目标逐条拆行（复用同一 pool_id 或按规则派生子序号），或在「关联链/发现」列用顿号分隔枚举；出现别名合并行（如 `PEND-DOTNET-003 又名 P3`）即口径违规，聚合与报告统计均不得计入。
- **计数三公式（2026-09-20，唯一口径）**：① `pool_total` = 唯一 pool_id 数（按 pool_id 去重后的行数，与状态分桶无关，分桶计数之和必须等于 pool_total）；② 各产物「发现统计表」计数 = 对应详情块实际枚举条目数（表内写 N 则正文必须有 N 个枚举块，逐条点名）；③ `closed` 计数 = 非误报非 pending 之和（closed = 全部条目 − 误报 − pending；pending 含 OPEN 与 DYNAMIC_VERIFIED 两种状态）。自报值与公式值不一致时，必须显式写出差异原因（哪一行/哪一条导致偏差），禁止静默取一；差异原因落点 = `pending_pool_{timestamp}.md` 聚合文件头「口径说明」节（2026-09-21）。
- **链状态口径（2026-09-21，公式③配套枚举登记）**：链状态四枚举——`closed` = 证据链闭合且非误报非 pending；`open` = 未闭合；`误报` = 证据否证；`pending` = 待补证池挂起（open 中已登记入 pending_pool 的部分；公式③口径下 pending 计数与 open 同集，closed = 全部 − 误报 − pending）。与 exploit-chain 四态映射（链路状态分解唯一口径）：

| exploit-chain 状态 | 链状态口径 |
| ---- | ---- |
| ✅ 已确认 | closed |
| ⚠️ 待验证 / 🔍 环境依赖 | open |
| ❌ 不可利用 | 误报 |

态名对照（2026-09-21）：公式③语境中的 `pending` 与本口径 `open` 同义同集（open 中已登记入 pending_pool 的部分）——公式③「closed = 全部条目 − 误报 − pending」即「closed = 全部条目 − 误报 − open」；引用 exploit-chain 产物做公式③核验时，四态分解中的 open 行即 pending 行。
- **pool 行先于引用（2026-09-20，强制）**：任何产物（含最终报告、exploit_chain、统计表、风险池节）引用 pool_id 之前，该 pool_id 必须已在本文件「## 本文件待补证池」节或 `pending_pool_{timestamp}.md` 聚合文件中登记（pool 行先于引用）；引用未登记 pool_id 即口径违规，须先补登记行再引用。
- **schema 扩展须先登记（2026-09-20）**：待补证池行格式（八字段）、闭合方式三枚举、条目状态枚举、pool_id 命名规则的任何扩展或变更，必须先登记进本文档本节（先登记后实施），不得先在产物中落新字段再补文档。

### 维度清单（执行真源快照，2026-09-21）

快照日期：2026-09-21。本清单是「维度核对」节（漏洞专项状态模型节）与专项强制枚举清单的**执行真源**：外部执行环境（无 `docs/` 目录）读本附录即可枚举全部维度。新增维度须先登记台账（`docs/新增Skill登记.md` 第二节，先登记后实施）并同步本快照；打包交付时对本快照与台账做对账（一致性人工核对记录）。清单完整性口径=台账全部审计质量机制条目（A/B 两类合计，新增即同步，禁止清单与台账漂移）。

维度分两类，三态/两态纪律不同（**维度分类不清的条目默认归 B 类**，从严解释：宁可多登记不可漏）：

#### A 类：漏洞机制维度（三态，否定证据纪律含范围 + rg 模式）

逐条三态：`覆盖`（附产物节位置）/ `否定证据`（NOT_APPLICABLE，含范围 + rg 模式）/ `不适用`（附判定理由）；禁止裸「未覆盖」「未提及」字样。

| # | 维度 | 归属专项（机制扩展落点） |
| ---- | ---- | ---- |
| A1 | 账号枚举·错误响应一致性 | dotnet-auth-audit（node-auth-audit 对称） |
| A2 | 审计完整性篡改 | dotnet-logging-audit（node 对称） |
| A3 | 审计可用性淹没 | dotnet-logging-audit（node 对称） |
| A4 | 签名请求重放保护（nonce/timestamp/replay cache freshness） | dotnet-crypto-audit + dotnet-webapi-audit（node 对称） |
| A5 | 整数溢出（数值边界） | dotnet-logic-audit（node 对称） |
| A6 | 配置暴露三维度：配置暴露 / 响应信息披露 / secret exposure 边界 | dotnet-config-audit（node 对称） |
| A7 | 供应链知识截止 + 离线来源（`knowledge_cutoff_date` / `offline_report_source`） | dotnet-vuln-scanner / node-vuln-scanner |
| A8 | 动态验证红线四零（零凭证/零网络/零服务/零 scratch 目录外写入） | pipeline 阶段 7 DYNAMIC_VERIFY(STATIC_UNIT) |

#### B 类：审计质量机制维度（两态：已落实 / 不适用附理由；登记式证据）

此类维度描述审计流程自身的失效链，不适用「rg 否定证据」三态；逐条登记两态之一——`已落实`（附登记式证据位置）/ `不适用`（附理由）。

| # | 维度 | 落点 |
| ---- | ---- | ---- |
| B1 | preflight 环境核查（模型枚举 / `.codegraph` 向上解析 / SDK 与运行时 / 凭证可用性声明） | 双 pipeline 阶段 0 |
| B2 | run_timestamp 统一下发（fullstack 编排层下发，子栈禁自产） | IO 全栈统一 run_timestamp 条款 |
| B3 | 维度核对自身（index「## 维度核对」节强制） | IO 漏洞专项状态模型节 |
| B4 | 待补证池八字段（含闭合方式与一 id 一行纪律） | IO 待补证风险池单一真源节 |
| B5 | 专项派发核对（index「## 专项派发核对」节三态） | IO 漏洞专项状态模型节 |
| B6 | 里程碑回写（manifest 里程碑行格式唯一真源） | PHASE_STATUS |
| B7 | 方法级配对（node route-mapper 禁双方法保守上界进下游） | node-route-mapper |
| B8 | 内嵌异栈三态归属决策表 | 双 pipeline 阶段 0 stack_detect |
| B9 | 阶段 0.7 递归 search_scope（六模式 + 目录枚举纪律） | 双 pipeline 阶段 0.7 |
| B10 | 阶段 6 执行顺序约束（P1-5：contract-mapper 先行，consistency-audit / taint-linker 按依赖序启动） | fullstack-audit-pipeline 阶段 6 |
| B11 | 等待超时公式（FULL 模式 `预计分钟 = 2 + 总文件数千分位 × 8`，取整与总文件数口径见 PHASE_STATUS 条款） | PHASE_STATUS 等待超时公式条款 |

### preflight 产物模板（2026-09-21）

`quality/preflight_{timestamp}.md`（node 镜像 `node/quality/preflight_{timestamp}.md`）固定结构如下，禁止自定义格式：

```md
# Preflight 环境核查
run_id: {project_name}_{run_timestamp}
run_timestamp: {YYYY_MM_DD_HH_mm}

## 四子项判定表
| 子项 | 结果(PASS/FAIL/DEGRADED) | 探测方法与范围 | 结论与影响 |
| ---- | ---- | ---- | ---- |
| 模型枚举 | PASS | 探测执行环境可用模型列表 | 指定模型可用，按原计划执行 |
| .codegraph 向上解析 | DEGRADED | 从 source_path 逐层向上解析 `.codegraph/`（含 x/y/.codegraph 嵌套层级） | 未定位已建索引，阶段 0 新建索引；回退静态分析 |
| SDK 与运行时 | DEGRADED | dotnet SDK / node 运行时与包管理器可用性（含版本与目标框架兼容说明） | SDK 不可用，静态审计继续并登记，涉及构建的检查降级 |
| 凭证可用性 | PASS | 声明本次执行可用凭证范围（无凭证须显式写「无」） | 无（阶段 7 动态验证与集成级补证不适用，红线四零前置） |

## 降级项清单
- {降级子项} | 原因 | 登记位置：manifest gate_reason | 影响阶段：{N}
- 无
```

四子项写法要点：

- **模型枚举**：列出探测到的可用模型；指定模型不可用时按可用列表降级，本表与 manifest `gate_reason` 双登记，禁止静默换模
- **`.codegraph` 向上解析**：写明解析起点、向上遍历的层级数与每一层判定结果；未定位时结论必须含「回退静态分析」字样，不得只写「未找到」
- **SDK 与运行时**：dotnet 侧含 SDK 版本与目标框架兼容性；node 侧含 node/npm/pnpm/yarn 与包管理器；不可用即 DEGRADED 并登记，静态审计路径不受影响
- **凭证可用性**：逐项枚举可用凭证类型与范围；无凭证显式写「无」，并注明阶段 7 动态验证（STATIC_UNIT 红线四零不受影响）与 needs-env 补证项的关系
- **级联规则（2026-09-21）**：SDK / 运行时不可用 → 静态审计继续执行，降级登记进 manifest `gate_reason`（不阻断后续静态阶段）；无凭证 → 不影响静态审计，仅阶段 7 动态验证与 needs-env 集成级补证项降级——红线四零是前置自检项，不因无凭证而放宽或豁免

fullstack 编排模式下 `{run_timestamp}` 一律取编排层下发值，禁止子栈自产（见「全栈统一 run_timestamp」条款）；任一降级项必须同时登记进 `quality/manifest_{run_id}.md` 的 `gate_reason`。
