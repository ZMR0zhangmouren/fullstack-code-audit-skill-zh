---
name: fullstack-audit-pipeline
description: dotnet + Node.js 全栈白盒安全审计唯一总入口。通过 output_path 目录隔离并行调度 dotnet-audit-pipeline 与 node-audit-pipeline，阶段 6 执行 cross-stack-contract-mapper 完成跨端契约对账，输出四完成态声明与全栈级 quality/ 收尾产物。
---

# 全栈代码安全审计总入口

目标：对同时包含 dotnet 后端与 Node.js 前端/BFF 的项目，输出一份可复核、可修复、可量化的全栈白盒审计报告。本 skill 是全栈唯一总编排入口，负责阶段 0 双栈技术栈识别、双栈并行调度、阶段 6 跨端关联、四完成态声明与全栈级收尾双保险。

## 输入

用户提供：

- `dotnet_source_path`：.NET 后端项目源码路径（解决方案目录、仓库根目录或单项目目录）。
- `node_source_path`：Node.js 前端/BFF 源码路径（仓库根目录或包含 `package.json` 的目录）。
- `stack_mode`：`BOTH | DOTNET_ONLY | NODE_ONLY`，默认 `BOTH`。
  - `BOTH`：双栈均审计。
  - `DOTNET_ONLY`：仅审计 dotnet 栈，Node.js 栈记录 `NOT_RUN + 原因`。
  - `NODE_ONLY`：仅审计 Node.js 栈，dotnet 栈记录 `NOT_RUN + 原因`。
- `output_root`：全栈输出根目录，默认 `{dotnet_source_path}_fullstack_audit`。
- `coverage_mode`：`FULL | SAMPLE | INCREMENTAL`，默认 `FULL`，透传给双栈子流水线各自生效。

派生变量（用于保证全栈产物可对齐）：

- `project_name`：从 `dotnet_source_path` 目录名提取（basename）。
- `timestamp` / `run_timestamp`：全栈统一生成时间戳，规范名 `run_timestamp`，建议格式 `YYYY_MM_DD_HH_mm`。由编排层生成后下发双栈子流水线，双栈全部产物命名一律使用 `run_timestamp`，禁止子栈各自独立生成时间戳；子栈实际启动时刻与 `run_timestamp` 的差异只在各自 `quality/manifest_*.md` 的映射表中登记体现（口径真源见 `IO_PATH_CONVENTION.md` 命名节）。
- `run_id`：建议 `{project_name}_{timestamp}` 或等价唯一标识，贯穿本次执行全程。

全局约束（正文重申）：

- **GC1 纯文档约束**：本 skill 及本次任务只允许创建/修改 `.md` 文件；禁止创建 `scripts/` 或任何可执行代码文件。本 skill 在当前安装形态下是“文档编排/方法论”版本，若环境中不存在对应执行器，直接按阶段化流程进行源码分析与报告生成。
- **GC6 排除规则**：Node.js 侧枚举时，`node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`、`coverage/` 目录不纳入审计面；`package-lock.json`/`yarn.lock`/`pnpm-lock.yaml` 作为 lockfile 例外，必须纳入供应链审计；**例外（2026-09-18）**：内嵌异栈项目不在 GC6 排除范围，按阶段 0 归属决策表处置。

## 阶段 0：双栈 stack-detect

目标：识别双栈技术栈与入口形态，为后续 adapter 选择、框架专项触发与覆盖口径调整提供依据。

1. **Node.js 技术栈检出**
   - 归属：node 侧 stack-detect 由 `node-audit-pipeline` 内建阶段 0 完成（skills/ 下无独立 node-stack-detect skill），全栈层不亲自调用，读取 `{output_root}/node/stack_detect/stack_detect_{timestamp}.md` 作为 node 栈技术栈依据，避免同一产物双写来源。
   - 输入（由 node-audit-pipeline 内建阶段 0 消费）：`node_source_path/package.json`。
   - 读取产物：`{output_root}/node/stack_detect/stack_detect_{timestamp}.md`。
   - 读取时须确认产物内容要点：Web/SSR/GraphQL 框架面、构建工具、SPA 降级标记、GC6 排除规则生效说明、内嵌异栈项目归属决策表；**产物缺失时不再静默回退**读取 node 侧 route_mapping 入口形态汇总——必须将该栈阶段 0 置 `BLOCKED` 并写入全栈 manifest `gate_reason`（写明缺项），待 node-audit-pipeline 补齐 `stack_detect_{timestamp}.md` 后重新读取，方可继续阶段 1。

2. **dotnet 技术栈/框架面识别**
   - dotnet 侧无独立 `dotnet-stack-detect` skill，由 `dotnet-audit-pipeline` 内部阶段 0 完成技术栈与框架面识别并强制交付 `stack_detect/stack_detect_{timestamp}.md`。
   - 全栈层读取 `{output_root}/dotnet/stack_detect/stack_detect_{timestamp}.md` 作为 dotnet 栈技术栈依据；**产物缺失时不再回退**读取 `framework_audit/` 框架识别结论或 route_mapping 入口形态汇总等效产物——必须置 `BLOCKED` 并写入全栈 manifest `gate_reason`（写明缺项），补齐后重新读取。

3. **单栈模式处理**
   - `stack_mode=DOTNET_ONLY` 时，Node.js 侧创建 `{output_root}/node/stack_detect/empty_result_{timestamp}.md`，写明 `execution_status=NOT_RUN`，原因=`stack_mode=DOTNET_ONLY`。
   - `stack_mode=NODE_ONLY` 时，dotnet 侧必须创建 `{output_root}/dotnet/stack_detect/empty_result_{timestamp}.md`，写明 `execution_status=NOT_RUN`，原因=`stack_mode=NODE_ONLY`。

4. **内嵌异栈项目检测（2026-09-18）**：node 仓库在 GC6 排除目录之外命中 `*.csproj`/`*.sln`/`*.fsproj`，或 dotnet 仓库命中含构建脚本引用的 `package.json`/`src/web/` 前端目录 → stack-detect 产物必须含「## 内嵌异栈项目」节，逐条按归属决策表三态登记（样例：随宿主审并标注「样例」/ 生产引用：提升为独立审计面并调度对应栈 pipeline / 仅文档：排除并记理由；不允许留空）。三态判定标准——样例：路径含 sample/demo/example 或 manifest 声明为示例，其发现按真实代码同等登记（样例私钥也登记）；生产引用：宿主代码实际引用其构建产物/路由/包，提升为独立审计面；仅文档：无构建产物且无宿主引用，排除并记理由。

阶段 0 输出：

- `{output_root}/node/stack_detect/stack_detect_{timestamp}.md`
- `{output_root}/dotnet/stack_detect/stack_detect_{timestamp}.md` 或 `empty_result_{timestamp}.md`（强制产物，缺失即 BLOCKED 写明缺项）
- `{output_root}/quality/manifest_{run_id}.md` 中阶段 0 标记为 `DONE`

**意图源递归探测（2026-09-18）**：全栈编排层阶段 0.7 下发 design_intent 产物时，否定结论必须附完整 `search_scope` 自证；子流水线复核不一致的回告必须写入全栈 manifest `gate_reason` 并阻塞该栈阶段 1 直至修正。

## 双栈并行调度（强制）

目标：在零改动 `dotnet-audit-pipeline` 本体的前提下，通过目录隔离并行驱动双栈子流水线。

1. **目录隔离原则**
   - `dotnet-audit-pipeline` 以 `output_path={output_root}/dotnet` 调用，其全部产物落入 `{output_root}/dotnet/` 子树。
   - `node-audit-pipeline` 以 `output_path={output_root}/node` 调用，其全部产物落入 `{output_root}/node/` 子树。
   - 显式声明：`dotnet-audit-pipeline` 本体零改动，仅通过 `output_path` 参数实现全栈目录隔离。

2. **参数透传**
   - 双栈各自接收：
     - `source_path` = `dotnet_source_path` / `node_source_path`
     - `output_path` = `{output_root}/dotnet` / `{output_root}/node`
     - `coverage_mode`（与全栈层一致）
   - 双栈子流水线内部自行生成 `run_id` 等价标识或复用全栈 `run_id`，但须在各自 `quality/manifest_*.md` 中记录与全栈 `run_id` 的映射关系。

3. **并行执行**
   - 逻辑上并行调度双栈子流水线；实际并发由执行环境决定。
   - 任一子流水线 `BLOCKED` 时，全栈层 `pipeline_execution` 不得标记为 `COMPLETED`。

4. **单栈模式处理**
   - `stack_mode=DOTNET_ONLY` 时，不调用 `node-audit-pipeline`；Node.js 子树通过空结果说明文件记录 `NOT_RUN` 原因。
   - `stack_mode=NODE_ONLY` 时，不调用 `dotnet-audit-pipeline`；dotnet 子树通过空结果说明文件记录 `NOT_RUN` 原因。

阶段 1–5 产物由双栈子流水线各自负责产出，全栈层只读取不干预：

- `{output_root}/dotnet/route_mapping/routes_{timestamp}.md`
- `{output_root}/dotnet/quality/api_coverage_gate_{timestamp}.md`
- `{output_root}/node/route_mapping/routes_{timestamp}.md`
- `{output_root}/node/quality/api_coverage_gate_{timestamp}.md`
- 以及两栈各自 `route_tracer/`、`vuln_audit/`、`vuln_poc/`、`framework_audit/`、`exploit_chain/`、`quality/` 等全部产物。

**里程碑回写（强制，替代轮询）**：
- 子流水线每完成一个阶段，须在各自 `quality/manifest_{run_id}.md` 追加一行里程碑，格式以 `skills/shared/PHASE_STATUS.md` 为唯一真源。
- 编排层等待方式 = 「子流水线完成汇报」触发 + 对 manifest 里程碑与关键产物的一次性终态核验；禁止「定时休眠 + 文件清点」的周期性磁盘轮询。
- 超时兜底：超过预期时长未收到汇报，才允许一次主动核查，并在 manifest 记录核查原因。预期时长口径以 `skills/shared/PHASE_STATUS.md` 为唯一真源：FULL 模式 `预计分钟 = 2 + 总文件数千分位 × 8`（每千文件约 8 分钟）。

**0.7 复核回告**：子流水线 `design_intent_recheck` 里程碑行格式——`阶段 0.7 复核: AGREE ({命中数}) | {timestamp}` 或 `阶段 0.7 复核: MISMATCH ({命中目录数}) | {timestamp}`（MISMATCH 时编排层必须修正 design_intent 产物后重新下发，禁止带错继续）。格式真源 PHASE_STATUS.md。

## 阶段 6：跨端关联

目标：以前端/BFF 出站调用与 dotnet 后端路由清单做跨端契约对账，识别隐藏攻击面与幽灵调用。

**执行顺序（强制，2026-09-18）**：P1 contract-mapper 先行——其产物 `api_contract_map_{timestamp}.md` 与 `contract_coverage_gate_{timestamp}.md` 落盘并核验后，方可启动第 3 条的 cross-stack-taint-linker 与 cross-stack-consistency-audit；后两者输入节必须显式列出 contract_map 产物路径。异常中断导致 consistency-audit 启动时 contract_map 缺失：允许先以「输入缺失」落盘，但全栈 coverage_consistency_check 必须二次消费回补（读取后到的 contract_map 更新结论），回补动作记入 manifest。

1. **P1 必须执行：cross-stack-contract-mapper**
   - 调用：`cross-stack-contract-mapper`。
   - 输入：
     - `{output_root}/dotnet/route_mapping/routes_{timestamp}.md`
     - `{output_root}/dotnet/route_mapping/params_{timestamp}.md`
     - `node_source_path`
     - `{output_root}/node/stack_detect/stack_detect_{timestamp}.md`
     - 反向代理/baseURL 环境变量证据（可选，有则必须记录来源）
   - 输出（按 `IO_PATH_CONVENTION.md` 落盘到 `{output_root}/cross/`）：
     - `{output_root}/cross/api_contract_map_{timestamp}.md`（matched / frontend_only / backend_only 三桶）
     - `{output_root}/cross/contract_coverage_gate_{timestamp}.md`（含 `contract_coverage_status`）
     - `{output_root}/cross_analysis/index_{timestamp}.md`（阶段索引）

1.5 **node-feature-api-mapper（P1.5，2026-09-19）**
   - 调用：`node-feature-api-mapper`（skills/ 下存在时；不存在记 NOT_RUN + 原因）。
   - 输入：`node_source_path`、`{output_root}/node/route_mapping/routes_{timestamp}.md`、`{output_root}/node/route_mapping/frontend_outbound_{timestamp}.md`、P1 产物 `{output_root}/cross/api_contract_map_{timestamp}.md`（matched 桶）、`{output_root}/node/design_intent/`（可选）。
   - 输出：`{output_root}/node/route_mapping/feature_api_map_{timestamp}.md`（+ PARTIAL 时 `unmapped_feature_calls_{timestamp}.md`）。
   - 语义：视图层参考，禁止作 EVID 证据源；`coverage_status` 不影响阶段 6 完成态，但 PARTIAL 时写入 gate_reason 备注。

2. **backend_only 隐藏攻击面处置**
   - `backend_only` 条目必须写入 dotnet 侧 `{output_root}/dotnet/cross_analysis/` 下的 high_risk_routes 或 sampled 变体，作为隐藏攻击面优先进入 dotnet route-tracer。
   - **trace 归属（2026-09-20）**：隐藏攻击面（backend_only）条目的 route trace 由**编排层直接执行**——阶段 6 执行时 dotnet 子流水线可能已退出，不得因此回退要求子流水线重启补跑；trace 质量门槛与子流水线内一致且不降低：每条 trace 必须含 `file:line` 证据与 trace 完整性声明，trace 契约段落（Sink Summary / 参数可控性矩阵 / Sink 定位 / Trace 完整性声明 / Sink Evidence Type Checklist）按 `dotnet-route-tracer` 模板逐段齐备。
   - 文件选择遵循 `IO_PATH_CONVENTION.md` 规则：dotnet 侧 `api_coverage_status=COMPLETE` 时写入 `high_risk_routes_{timestamp}.md`；`api_coverage_status=PARTIAL` 或 `coverage_mode=SAMPLE` 时写入 `sampled_high_risk_routes_{timestamp}.md`。
   - 在最终报告 `2.2) 隐藏攻击面清单` 中全量逐条列出，且 `contract_backend_only_count` 必须与清单条目总数一致。

3. **跨端三件套（taint-linker 与 consistency-audit，ACTIVE；依赖 P1 contract_map 产物启动）**
   - 调用 `cross-stack-taint-linker`：输入 `contract_map`，输出 `{output_root}/cross/cross_taint_links_{timestamp}.md`（cross_taint_links），XTRACE 链聚合入 `{output_root}/cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md`。
   - 调用 `cross-stack-consistency-audit`：输出 `{output_root}/cross/consistency_findings_{timestamp}.md`（consistency_findings），供全栈层 coverage_consistency_check 补充。
   - `cross_stack_exploit_chains_{timestamp}.md` 的 `linker_status` 由 `NOT_EXECUTED` 更新为 `EXECUTED`。

阶段 6 输出：

- `{output_root}/cross/api_contract_map_{timestamp}.md`
- `{output_root}/cross/contract_coverage_gate_{timestamp}.md`
- `{output_root}/cross/cross_taint_links_{timestamp}.md`
- `{output_root}/cross/consistency_findings_{timestamp}.md`
- `{output_root}/cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md`（跨端利用链正式产物；无跨端链时以 `empty_result_{timestamp}.md` 记录 `NOT_APPLICABLE`）
- `{output_root}/cross_analysis/index_{timestamp}.md`

## 全栈门禁与四完成态声明（强制）

目标：在子流水线各自完成态基础上，聚合为全栈统一的四完成态声明，禁止用单一“已完成”替代。

1. **四完成态声明字段（逐字，不得改写）**
   - `dotnet_api_coverage_status`：来自 `{output_root}/dotnet/quality/api_coverage_gate_{timestamp}.md`，取值为 `COMPLETE | PARTIAL`。
   - `node_api_coverage_status`：来自 `{output_root}/node/quality/api_coverage_gate_{timestamp}.md`，取值为 `COMPLETE | PARTIAL`。
   - `contract_coverage_status`：来自 `{output_root}/cross/contract_coverage_gate_{timestamp}.md`，取值为 `COMPLETE | PARTIAL`。
   - `audit_surface_status`：全栈漏洞/框架专项覆盖状态，取值为 `COMPLETED | PARTIAL | INITIAL_SCREENED`。
   - `audit_surface_status` 聚合规则：由双栈子流水线各自 `audit_surface_status`（来自各自 `quality/manifest_*.md` 或最终报告）取弱栈聚合——任一为 `PARTIAL` → `PARTIAL`；双栈均 `COMPLETED` → `COMPLETED`；任一为 `INITIAL_SCREENED` 且无 `PARTIAL` → `INITIAL_SCREENED`。取弱来源必须在 `gate_reason` 中注明（如 `dotnet_audit_surface_status=PARTIAL 来源`）。
   - `audit_surface_status=COMPLETED` 的前置条件：跨端链产物 `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` 已生成（无跨端链时以 `empty_result_{timestamp}.md` 记录 NOT_APPLICABLE）；链存在但含 `推断可行/理论可行` 环节时，`audit_surface_status` 不得高于 `PARTIAL`。

2. **全栈级覆盖门禁摘要（建议写入 `{output_root}/quality/fullstack_gate_{timestamp}.md` 并最终报告 `2) 覆盖门禁摘要`）**
   - `dotnet_api_coverage_percent`
   - `node_api_coverage_percent`
   - `pipeline_execution`：`COMPLETED | PARTIAL`。判定口径按 `coverage_mode` 区分：
     - `coverage_mode=FULL`：仅当四声明全部为 `COMPLETE`/`COMPLETED` 且无 `BLOCKED` 时才允许 `COMPLETED`。
     - `coverage_mode=INCREMENTAL`：当双栈子流水线各自 `api_coverage_status=COMPLETE`（变更集合含扩展调用链内 100% 覆盖，对齐 `node-audit-pipeline` 与 `IO_PATH_CONVENTION.md` 门禁口径）、四声明全部为 `COMPLETE`/`COMPLETED` 且无 `BLOCKED` 时允许 `COMPLETED`；且全栈最终报告必须声明 `coverage_mode=INCREMENTAL`、增量基线（变更 commit 范围）、受影响文件数/总文件数，并引用双栈 `quality/incremental_scope_{timestamp}.md` 与 `unmapped_routes_{timestamp}.md` 产物，禁止"全量审计完成"措辞。
     - `coverage_mode=SAMPLE`：`pipeline_execution` 禁止为 `COMPLETED`，最高 `PARTIAL`。
   - `gate_decision`：`ALLOW_COMPLETED | FORCE_PARTIAL`。判定条件：四声明全部为 `COMPLETE`/`COMPLETED` 且符合当前 `coverage_mode` 门禁（`FULL` 全量覆盖；`INCREMENTAL` 变更集内 100% 覆盖且完成增量基线声明）→ `ALLOW_COMPLETED`；否则 → `FORCE_PARTIAL`。
   - `gate_reason`：`FORCE_PARTIAL` 时写明具体阻断来源——四声明中具体为 `PARTIAL` 的字段、`BLOCKED` 子流水线、`coverage_mode=SAMPLE`，或 INCREMENTAL 下变更集未全量覆盖的情形；同时注明 `audit_surface_status` 取弱来源。
   - `unmapped_routes_source`：`{dotnet|node}/quality/unmapped_routes_{timestamp}.md` 实际路径；若双栈均未 `PARTIAL` 则写 `N/A`。

3. **跨端契约覆盖摘要（最终报告 `2.1)`）**
   - `contract_coverage_percent`、`contract_matched_count`、`contract_frontend_only_count`、`contract_backend_only_count` 必须直接引用 `{output_root}/cross/contract_coverage_gate_{timestamp}.md` 中的三桶计数。
   - `contract_map_source` 禁止 `N/A`；若 `contract_coverage_status=PARTIAL` 必须指向 `{output_root}/cross/api_contract_map_{timestamp}.md` 实际产物或补图计划。
   - `coverage_mode=INCREMENTAL` 时的对账口径：仅对变更集涉及的前后端调用（变更文件集 + 扩展受影响调用链）进行契约对账，`contract_coverage_percent` 以变更集内前后端调用为分母计算；若变更集不涉及跨端调用，须在 `{output_root}/cross/contract_coverage_gate_{timestamp}.md` 中显式声明对账范围限制与原因，不得与 FULL 全量对账口径混用。

4. **阻断联动规则**
   - `dotnet_api_coverage_status != COMPLETE` 或 `node_api_coverage_status != COMPLETE` 或 `contract_coverage_status != COMPLETE` 时，`pipeline_execution` 禁止为 `COMPLETED`。
   - `coverage_mode = SAMPLE` 时，`pipeline_execution` 禁止为 `COMPLETED`。
   - `coverage_mode = INCREMENTAL` 时，若变更集合（含扩展调用链）内双栈任一 `api_coverage_status != COMPLETE`，`pipeline_execution` 禁止为 `COMPLETED`（与 FULL 的差异在覆盖范围，不在判定逻辑）。
   - 禁止用“审计完成”单一语句替代四完成态声明。

## 收尾双保险（强制）

目标：在全栈层再次执行一致性核对 → 快速校验 → 利用链聚合 → 最终报告 → 收尾锚点清单，确保跨端字段对齐、BLOCKED 联动生效。

1. **待补证池聚合（先行，2026-09-18）**：扫描全部产物「## 本文件待补证池」节，聚合生成 `{output_root}/quality/pending_pool_{timestamp}.md`（含 `pool_total`、聚合时间、来源清单）；最终报告风险池节只引用该文件。

2. **全栈一致性核对（consistency_check）**
   - 生成 `{output_root}/quality/coverage_consistency_check_{timestamp}.md`。
   - 核对范围至少包括：
     - `dotnet_api_coverage_status` / `node_api_coverage_status` / `contract_coverage_status` / `audit_surface_status` 在 gate、cross/contract_coverage_gate、最终报告之间一致。
     - `contract_map` 三桶计数（`matched_count`/`frontend_only_count`/`backend_only_count`）与最终报告 `2.1)` 计数一致。
     - exploit-chain 总览表统计与最终报告 `exploit_chain_consistency_check_counts` 一致。
   - 输出 `consistency_check_status`：`PASS | BLOCKED`。

3. **快速校验（quick_validation）**
   - 生成 `{output_root}/quality/quick_validation_{timestamp}.md`。
   - `quick_validation.final_decision` 必须与 `consistency_check_status` 联动：若 `consistency_check_status=BLOCKED`，则 `final_decision` 必须为 `BLOCKED`。

4. **利用链聚合（exploit_chain）**
   - 生成 `{output_root}/exploit_chain/exploit_chains_{timestamp}.md`，聚合双栈子流水线已产出的单栈利用链，并透传 `coverage_mode`、`api_coverage_status` 等覆盖口径。
   - 生成 `{output_root}/cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md`（正式产物）：聚合 `cross-stack-taint-linker` 的 XTRACE 链，逐链按三档标注 `feasibility`（确认可行/推断可行/理论可行）；无跨端链时以 `empty_result_{timestamp}.md` 记录 `NOT_APPLICABLE`。
   - 若 `consistency_check_status=BLOCKED`，exploit-chain 链路可行性不得标记为“确认可行”。

5. **最终报告（final_report）**
   - 生成 `{output_root}/{project_name}_代码审计_{timestamp}.md`。
   - 质量章节必须复用 `skills/shared/FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE.md` 固定字段。
   - 必须包含四完成态声明、跨端契约覆盖摘要、隐藏攻击面清单、跨端利用链、一致性核对摘要、收尾锚点检查结果引用。
   - `coverage_mode=INCREMENTAL` 时，最终报告必须声明增量基线与覆盖范围：`coverage_mode=INCREMENTAL`、变更基线（commit 范围）、受影响文件数/总文件数，并引用双栈 `quality/incremental_scope_{timestamp}.md` / `unmapped_routes_{timestamp}.md` 产物，禁止“全量审计完成”措辞。

6. **收尾锚点检查清单（final_anchor_checklist）**
   - 生成 `{output_root}/quality/final_anchor_checklist_{timestamp}.md`。
   - 在 dotnet 与 node 子流水线锚点行之外，必须增加跨端锚点行：
     - [ ] `cross/api_contract_map_{timestamp}.md` 三桶计数与最终报告 `2.1)` 计数对账一致。
     - [ ] `cross/contract_coverage_gate_{timestamp}.md` 的 `contract_coverage_status` 已确认。
   - 汇总区块：
     - `checklist_pass_count`
     - `checklist_blocked_count`
     - `checklist_pending_count`
     - `final_anchor_decision`：`PASS | BLOCKED | PENDING`
   - 若 `checklist_blocked_count > 0`，`final_anchor_decision` 必须为 `BLOCKED`。
   - 最终报告 `4.6)` 字段必须与 checklist 汇总区块逐字段对齐。

## 输出

全栈层必须真实创建以下目录与关键产物：

```
{output_root}/
├── dotnet/                          # dotnet-audit-pipeline 产物子树（output_path 隔离）
│   ├── stack_detect/                # 技术栈识别产物（强制交付项）或 empty_result_{timestamp}.md
│   ├── route_mapping/
│   ├── auth_audit/
│   ├── route_tracer/
│   ├── vuln_audit/
│   ├── vuln_poc/
│   ├── framework_audit/
│   ├── cross_analysis/
│   ├── vuln_report/
│   ├── exploit_chain/
│   ├── global_sink_fallback/
│   └── quality/
├── node/                            # node-audit-pipeline 产物子树（output_path 隔离）
│   ├── stack_detect/
│   ├── route_mapping/
│   ├── auth_audit/
│   ├── route_tracer/
│   ├── vuln_audit/
│   ├── vuln_poc/
│   ├── framework_audit/
│   ├── cross_analysis/
│   ├── vuln_report/
│   ├── exploit_chain/
│   ├── global_sink_fallback/
│   └── quality/
├── cross/                           # 跨端产物
│   ├── api_contract_map_{timestamp}.md
│   ├── contract_coverage_gate_{timestamp}.md
│   ├── cross_taint_links_{timestamp}.md
│   ├── consistency_findings_{timestamp}.md
│   └── exploit_chain/
│       └── cross_stack_exploit_chains_{timestamp}.md（跨端利用链正式产物）
├── cross_analysis/
│   └── index_{timestamp}.md
├── exploit_chain/
│   └── exploit_chains_{timestamp}.md（双栈利用链聚合）
├── quality/                         # 全栈级 quality 产物
│   ├── manifest_{run_id}.md
│   ├── pipeline_execution_{timestamp}.md
│   ├── fullstack_gate_{timestamp}.md（建议）
│   ├── coverage_consistency_check_{timestamp}.md
│   ├── quick_validation_{timestamp}.md
│   └── final_anchor_checklist_{timestamp}.md
└── {project_name}_代码审计_{timestamp}.md   # 全栈最终报告
```

关键产物说明：

| 产物 | 路径 | 说明 |
| ---- | ---- | ---- |
| 全栈 manifest | `quality/manifest_{run_id}.md` | 阶段状态机、四完成态声明、中断点与下一步动作 |
| 全栈执行清单 | `quality/pipeline_execution_{timestamp}.md` | Skill 跟踪、stack_mode、覆盖口径、子流水线状态 |
| 全栈覆盖门禁摘要 | `quality/fullstack_gate_{timestamp}.md` | 建议产物，汇总双栈 api_coverage_status 与 contract_coverage_status |
| 一致性核对 | `quality/coverage_consistency_check_{timestamp}.md` | 跨 gate/trace/exploit/final report 字段冲突定位 |
| 快速校验 | `quality/quick_validation_{timestamp}.md` | 交付前最后一跳核验，`final_decision` 与 consistency_check 联动 |
| 利用链聚合 | `exploit_chain/exploit_chains_{timestamp}.md` | 双栈利用链聚合 |
| 跨端利用链 | `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` | 正式产物（cross-stack-taint-linker 聚合）；无跨端链时 `empty_result` 记录 NOT_APPLICABLE |
| 跨端契约对账 | `cross/api_contract_map_{timestamp}.md` | matched / frontend_only / backend_only 三桶 |
| 契约覆盖门禁 | `cross/contract_coverage_gate_{timestamp}.md` | 含 `contract_coverage_status` 与三桶计数 |
| 全栈最终报告 | `{project_name}_代码审计_{timestamp}.md` | 必须复用 `FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE.md` |

约束：

- 所有空结果或未执行阶段必须创建 `index_{timestamp}.md` 或 `empty_result_{timestamp}.md` 说明 `NOT_RUN` 原因，不得缺目录。
- 最终报告必须同时声明 `dotnet_api_coverage_status`、`node_api_coverage_status`、`contract_coverage_status`、`audit_surface_status`，禁止用单一“已完成”替代。
- 全栈统一 `run_timestamp`：本目录树全部 `{timestamp}` 产物名（`dotnet/`、`node/`、`cross/`、`quality/` 子树及全栈最终报告）一律使用编排层下发双栈的 `run_timestamp` 命名；子栈实际启动差异只在各自 `quality/manifest_*.md` 映射表登记，不得引入第二时间戳命名产物（真源见 `IO_PATH_CONVENTION.md` 命名节）。
