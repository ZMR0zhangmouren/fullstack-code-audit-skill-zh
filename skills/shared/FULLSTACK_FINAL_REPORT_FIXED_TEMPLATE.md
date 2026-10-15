# 全栈最终报告固定模板（质量章节）

用途：提供全栈模式（dotnet + Node.js）最终报告中“质量报告章节（固定）”的单一真源模板，避免字段遗漏与口径漂移。

继承来源：`skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md`（结构单一真源，BLOCKED 语义原样继承）。

建议嵌入：`{project_name}_代码审计_{timestamp}.md`

## 固定模板（强制字段）

```md
## 质量报告章节（固定）

### 1) 完成态四声明
- dotnet_api_coverage_status: {COMPLETE|PARTIAL}
- node_api_coverage_status: {COMPLETE|PARTIAL}
- contract_coverage_status: {COMPLETE|PARTIAL}
- audit_surface_status: {COMPLETED|PARTIAL|INITIAL_SCREENED}
- coverage_mode: {FULL|SAMPLE|INCREMENTAL}

### 2) 覆盖门禁摘要
- dotnet_api_coverage_percent: {n}%
- node_api_coverage_percent: {n}%
- pipeline_execution: {COMPLETED|PARTIAL}
- gate_decision: {ALLOW_COMPLETED|FORCE_PARTIAL}
- gate_reason: {text}
- unmapped_routes_source: quality/unmapped_routes_{timestamp}.md（若 dotnet_api_coverage_status=PARTIAL 或 node_api_coverage_status=PARTIAL 必填；否则写 N/A）

### 2.1) 跨端契约覆盖摘要
- contract_coverage_percent: {n}%
- contract_matched_count: {n}
- contract_frontend_only_count: {n}
- contract_backend_only_count: {n}
- contract_map_source: cross/api_contract_map_{timestamp}.md（禁止 N/A；若 contract_coverage_status=PARTIAL 必须指向实际产物或补图计划）

### 2.2) 隐藏攻击面清单
- backend_only_attack_surface:
  - route: {path}
    method: {HTTP_METHOD}
    auth_status: {PUBLIC|AUTHENTICATED|UNKNOWN}
    in_trace_pool: {true|false}
    notes: {text}
  - ...（backend_only 全量逐条列出）

### 2.3) 跨端利用链
- cross_stack_exploit_chain_source: cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md
- cross_stack_chain_status: {COMPLETED|PARTIAL|PENDING}
- xtrace_chains:
  - XTRACE-{id}: {description}
    feasibility: {确认可行|推断可行|理论可行}
    linker_status: {EXECUTED|NOT_EXECUTED}
    notes: {text}
  - ...
- cross-stack-taint-linker 已交付（ACTIVE）：跨端链由其聚合产出；无跨端链时 `empty_result` 记录 NOT_APPLICABLE，`linker_status` 保持 `NOT_EXECUTED`

### 3) 覆盖口径声明（必须保留）
- 若 coverage_mode=SAMPLE 或 dotnet_api_coverage_status=PARTIAL 或 node_api_coverage_status=PARTIAL：
  本报告仅代表“已映射入口”审计结论，不代表全量活动 API 结论。
- 若 coverage_mode=INCREMENTAL：
  本报告必须声明增量基线（变更 commit 范围）、受影响文件数/总文件数，并引用双栈 `quality/incremental_scope_{timestamp}.md` 与 `unmapped_routes_{timestamp}.md` 产物，禁止“全量审计完成”措辞。
- 若 contract_coverage_status=PARTIAL：
  本报告跨端契约覆盖不完整，隐藏攻击面清单中的 backend_only 条目可能未被充分追踪。

### 4) exploit-chain 覆盖口径摘要（固定）
- exploit_chain_source: exploit_chain/exploit_chains_{timestamp}.md
- exploit_chain_coverage_mode: {FULL|SAMPLE}
- exploit_chain_api_coverage_status: {COMPLETE|PARTIAL}
- exploit_chain_api_coverage_percent: {n}%
- exploit_chain_sampled_scope: {true|false}

### 4.5) 一致性核对摘要（建议）
- consistency_check_source: quality/coverage_consistency_check_{timestamp}.md（若存在）
- consistency_check_status: {PASS|BLOCKED|N/A}
- exploit_chain_consistency_check_counts: {PASS:n, BLOCKED:n, N/A:n}

### 4.6) 收尾锚点检查结果引用（建议）
- final_anchor_checklist_source: quality/final_anchor_checklist_{timestamp}.md（若存在）
- final_anchor_decision: {PASS|BLOCKED|PENDING|N/A}
- final_anchor_checklist_counts: {PASS:n, BLOCKED:n, PENDING:n}

### 5) Skill 使用跟踪与问题发现表（强制）

最终报告使用中文输出，除非必要的内容可以使用英文外。
最开始必须包含一张 Skill 使用与发现矩阵，覆盖所有已纳入本项目执行范围的 dotnet-* 与 node-* skills。

推荐字段：

| skill_name       | skill_type | execution_status | findings_status    | primary_outputs                        | depends_on                    | notes |
| ---------------- | ---------- | ---------------- | ------------------ | -------------------------------------- | ----------------------------- | ----- |
| dotnet-sql-audit | vuln_audit | COMPLETED        | FOUND / NO_FINDING | vuln_audit/sql_*.md; vuln_poc/sql_*.md | route_tracer; framework_audit | -     |
| node-sql-audit   | vuln_audit | COMPLETED        | FOUND / NO_FINDING | vuln_audit/sql_*.md; vuln_poc/sql_*.md | route_tracer; framework_audit | -     |

字段解释：

- skill_name：具体 Skill 名称
- skill_type：framework_audit / vuln_audit / route_tracer / mapping / dependency_scan / contract_linker 等
- execution_status：NOT_RUN / INITIAL_SCREENED / PARTIAL / COMPLETED / NOT_APPLICABLE
- findings_status：FOUND / NO_FINDING / PENDING_VERIFICATION / ENVIRONMENT_DEPENDENT
- primary_outputs：本 Skill 生成或主消费的文件
- depends_on：其依赖的前置阶段或关键产物
- notes：阻断原因、复核建议、环境限制、证据缺口

其中“其他漏洞类型”如果只是跑了抓手初筛，没有完成完整专项分析，必须明确标记为 INITIAL_SCREENED；如果已进入专项分析但未完成闭环，必须标记为 PARTIAL。

### 6) 漏洞列表总览

**分级详略规则（强制）**：
- 定级枚举闭合（2026-09-20）：严重等级只允许 `C` / `H` / `M` / `L` 四值；边界情形使用升级通道注记格式 `L（建议升 M，理由：…）`，禁止区间值（「L-M」为反例，不合规，真源见 `SEVERITY_RATING.md` 定级枚举闭合节）。
- H 级 + 关键 M 级（已确认可利用 / 跨端链已闭合）：全详情块（固定结构不变）。
- 普通 M 级：详情块压缩为「证据三段 + 修复建议」，sink 细节用专项产物引用替代。
- L 级：仅表格行（编号 / 等级 / 标题 / file:line / 专项产物引用），不写详情块。
- 待确认 / 风险池项：只入风险池表（§7 或对应节），正文不给详情。
- 详略不减免可追溯性：每条漏洞必须能从报告定位到专项产物（路径 + 锚点）。

（引用 vuln_audit/* 与 vuln_poc/* 结论，参照漏洞详情模板填写漏洞详情）

### 7) Trace 未闭合 / 待补证风险池
（列出 route_id 或 SINK_ONLY 合成 ID、缺失证据与建议动作）
```

## 验收要点

- `dotnet_api_coverage_status != COMPLETE` 或 `node_api_coverage_status != COMPLETE` 时，`pipeline_execution` 禁止为 `COMPLETED`
- `coverage_mode = SAMPLE` 时，`pipeline_execution` 禁止为 `COMPLETED`
- `dotnet_api_coverage_status = PARTIAL` 或 `node_api_coverage_status = PARTIAL` 时，`unmapped_routes_source` 不得为 N/A，必须指向实际产物文件
- `contract_coverage_status = PARTIAL` 时，`contract_map_source` 不得为 N/A，必须指向 `cross/api_contract_map_{timestamp}.md` 实际产物或补图计划文件
- `contract_backend_only_count` 必须与“隐藏攻击面清单”中 backend_only 条目总数一致
- `exploit_chain_consistency_check_counts` 必须与 `exploit_chain` 总览表统计一致
- 若 `consistency_check_status=BLOCKED`，`quick_validation.final_decision` 必须联动为 `BLOCKED`
- 若 `consistency_check_status=BLOCKED`，跨端利用链可行性不得写为“确认可行”
- 若存在 `final_anchor_checklist_{timestamp}.md`，建议最终报告回写其 `final_anchor_decision` 与 PASS/BLOCKED/PENDING 计数

## 最小示例（可复制）

```md
## 质量报告章节（固定）

### 1) 完成态四声明
- dotnet_api_coverage_status: PARTIAL
- node_api_coverage_status: COMPLETE
- contract_coverage_status: PARTIAL
- audit_surface_status: PARTIAL
- coverage_mode: SAMPLE

### 2) 覆盖门禁摘要
- dotnet_api_coverage_percent: 88%
- node_api_coverage_percent: 100%
- pipeline_execution: PARTIAL
- gate_decision: FORCE_PARTIAL
- gate_reason: dotnet_api_coverage_status=PARTIAL
- unmapped_routes_source: quality/unmapped_routes_2026_08_22_10_20.md

### 2.1) 跨端契约覆盖摘要
- contract_coverage_percent: 75%
- contract_matched_count: 45
- contract_frontend_only_count: 5
- contract_backend_only_count: 10
- contract_map_source: cross/api_contract_map_2026_08_22_10_20.md

### 2.2) 隐藏攻击面清单
- backend_only_attack_surface:
  - route: /api/v1/admin/legacy-sync
    method: POST
    auth_status: AUTHENTICATED
    in_trace_pool: false
    notes: 前端未引用，已纳入待补证风险池
  - route: /internal/health/detailed
    method: GET
    auth_status: PUBLIC
    in_trace_pool: true
    notes: 已进 trace 池，等待 route-tracer 闭合

### 2.3) 跨端利用链
- cross_stack_exploit_chain_source: cross/exploit_chain/cross_stack_exploit_chains_2026_08_22_10_20.md
- cross_stack_chain_status: PENDING
- xtrace_chains:
  - XTRACE-001: 前端登录表单 → Node.js BFF → dotnet AuthService 令牌生成
    feasibility: 推断可行
    linker_status: EXECUTED
    notes: taint-linker 已拼接跨端污点链，动态复核待执行

### 3) 覆盖口径声明（必须保留）
- 本报告仅代表“已映射入口”审计结论，不代表全量活动 API 结论。
- 本报告跨端契约覆盖不完整，隐藏攻击面清单中的 backend_only 条目可能未被充分追踪。

### 4) exploit-chain 覆盖口径摘要（固定）
- exploit_chain_source: exploit_chain/exploit_chains_2026_08_22_10_20.md
- exploit_chain_coverage_mode: SAMPLE
- exploit_chain_api_coverage_status: PARTIAL
- exploit_chain_api_coverage_percent: 88%
- exploit_chain_sampled_scope: true

### 4.5) 一致性核对摘要（建议）
- consistency_check_source: quality/coverage_consistency_check_2026_08_22_10_20.md
- consistency_check_status: PASS
- exploit_chain_consistency_check_counts: {PASS:3, BLOCKED:0, N/A:1}

### 4.6) 收尾锚点检查结果引用（建议）
- final_anchor_checklist_source: quality/final_anchor_checklist_2026_08_22_10_20.md
- final_anchor_decision: PASS
- final_anchor_checklist_counts: {PASS:5, BLOCKED:0, PENDING:0}

### 5) Skill 使用跟踪与问题发现表（强制）
（填写 skill_name / skill_type / execution_status / findings_status / primary_outputs / depends_on / notes）

### 6) 漏洞列表总览
（引用 vuln_audit/* 与 vuln_poc/*）

### 7) Trace 未闭合 / 待补证风险池
（列出 route_id / SINK_ONLY 与建议动作）
```

## BLOCKED 最小示例（计数对账失败）

用途：训练执行人识别“最终报告字段已写出，但 consistency 计数仍不可交付”的阻断场景。

```md
## 质量报告章节（固定）

### 1) 完成态四声明
- dotnet_api_coverage_status: PARTIAL
- node_api_coverage_status: COMPLETE
- contract_coverage_status: PARTIAL
- audit_surface_status: PARTIAL
- coverage_mode: SAMPLE

### 2) 覆盖门禁摘要
- dotnet_api_coverage_percent: 88%
- node_api_coverage_percent: 100%
- pipeline_execution: PARTIAL
- gate_decision: FORCE_PARTIAL
- gate_reason: dotnet_api_coverage_status=PARTIAL
- unmapped_routes_source: quality/unmapped_routes_2026_08_22_18_10.md

### 2.1) 跨端契约覆盖摘要
- contract_coverage_percent: 75%
- contract_matched_count: 45
- contract_frontend_only_count: 5
- contract_backend_only_count: 10
- contract_map_source: cross/api_contract_map_2026_08_22_18_10.md

### 2.2) 隐藏攻击面清单
- backend_only_attack_surface:
  - route: /api/v1/admin/legacy-sync
    method: POST
    auth_status: AUTHENTICATED
    in_trace_pool: false
    notes: 前端未引用，已纳入待补证风险池
  - route: /internal/health/detailed
    method: GET
    auth_status: PUBLIC
    in_trace_pool: true
    notes: 已进 trace 池，等待 route-tracer 闭合

### 2.3) 跨端利用链
- cross_stack_exploit_chain_source: cross/exploit_chain/cross_stack_exploit_chains_2026_08_22_18_10.md
- cross_stack_chain_status: PENDING
- xtrace_chains:
  - XTRACE-001: 前端登录表单 → Node.js BFF → dotnet AuthService 令牌生成
    feasibility: 理论可行（计数对账失败，自动降级）
    linker_status: EXECUTED
    notes: consistency_check_status=BLOCKED → 可行性降级，禁止"确认可行"措辞

### 3) 覆盖口径声明（必须保留）
- 本报告仅代表“已映射入口”审计结论，不代表全量活动 API 结论。
- 本报告跨端契约覆盖不完整，隐藏攻击面清单中的 backend_only 条目可能未被充分追踪。

### 4) exploit-chain 覆盖口径摘要（固定）
- exploit_chain_source: exploit_chain/exploit_chains_2026_08_22_18_10.md
- exploit_chain_coverage_mode: SAMPLE
- exploit_chain_api_coverage_status: PARTIAL
- exploit_chain_api_coverage_percent: 88%
- exploit_chain_sampled_scope: true

### 4.5) 一致性核对摘要（建议）
- consistency_check_source: quality/coverage_consistency_check_2026_08_22_18_10.md
- consistency_check_status: BLOCKED
- exploit_chain_consistency_check_counts: {PASS:3, BLOCKED:0, N/A:1}

### 4.6) 收尾锚点检查结果引用（建议）
- final_anchor_checklist_source: quality/final_anchor_checklist_2026_08_22_18_10.md
- final_anchor_decision: BLOCKED
- final_anchor_checklist_counts: {PASS:3, BLOCKED:1, PENDING:1}

### 5) Skill 使用跟踪与问题发现表（强制）
（填写 skill_name / skill_type / execution_status / findings_status / primary_outputs / depends_on / notes）

### 6) 漏洞列表总览
（引用 vuln_audit/* 与 vuln_poc/*）

### 7) Trace 未闭合 / 待补证风险池
（列出 route_id / SINK_ONLY 与建议动作）
```

#### BLOCKED 示例判定说明（仅适用于上方 BLOCKED 最小示例）

- 若 `consistency_check_status=BLOCKED`，则该示例不可交付
- 若 `exploit_chain_consistency_check_counts` 与 exploit_chain 总览表统计不一致，必须先回写最终报告，再重跑 `quick_validation`
- 若存在 BLOCKED，exploit-chain 链路结论不得写为“确认可行”
- 若契约对账存在阻断（`contract_coverage_gate` 判定为 BLOCKED，如 `contract_map_source` 指向空文件），或 `consistency_check_status=BLOCKED` 时，contract 覆盖结论按 gate 判定降级为 PARTIAL；四声明中 `contract_coverage_status` 不得为 COMPLETE

## 漏洞详情模板（强制使用）

> 在 **固定模板（强制字段）** 的 **### 6) 漏洞列表总览** 中使用。

### 每条漏洞详情结构（强制）

每条漏洞必须遵循以下结构（写入本次总报告的漏洞详情段落）：

```markdown
### [{等级前缀}-{类型代码}-{序号}] {风险标题}

| 项目 | 信息 |
|------|------|
| 严重等级 | {🔴/🟠/🟡/🔵} (CVSS {score}) |
| 可达性 (R) | {0-3} - {理由} |
| 影响范围 (I) | {0-3} - {理由} |
| 利用复杂度 (C) | {0-3} - {理由} |
| 可利用性 | ✅ 已确认 / ⚠️ 待验证 / ❌ 不可利用 / 🔍 环境依赖 |
| 位置 | {文件路径}:{行号} ({函数/方法}) |

#### 数据流链（Source → Sink）
```

(按路由逐行写出赋值/传递/拼接/校验/分支，禁止省略)

#### 可利用前置条件

- 鉴权要求：{无需/需登录/需特定权限}
- 输入可控性：{完全可控/条件可控/不可控}
- 触发条件：{分支/异常/环境依赖}

#### 验证 PoC（强制给出可执行请求）

```http
{HTTP Method} {完整路径与查询/Body} HTTP/1.1
Host: {host}
{必要 Header/Session/JWT/Cookie}

{Payload}
```

#### 建议修复

```
- 以"代码替换建议"为主（给出安全写法要点）
- 给出"如何在代码中搜索修复是否遗漏"的搜索语句（bash/rg 形式）
```
