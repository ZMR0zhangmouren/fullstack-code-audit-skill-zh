# .NET 最终报告固定模板（质量章节）

用途：提供最终报告中“质量报告章节（固定）”的单一真源模板，避免字段遗漏与口径漂移。

建议嵌入：`{project_name}_代码审计_{timestamp}.md`

## 固定模板（强制字段）

```md
## 质量报告章节（固定）

### 1) 完成态双声明
- audit_surface_status: {COMPLETED|PARTIAL|INITIAL_SCREENED}
- api_coverage_status: {COMPLETE|PARTIAL}
- coverage_mode: {FULL|SAMPLE}

### 2) 覆盖门禁摘要
- api_coverage_percent: {n}%
- pipeline_execution: {COMPLETED|PARTIAL}
- gate_decision: {ALLOW_COMPLETED|FORCE_PARTIAL}
- gate_reason: {text}
- unmapped_routes_source: quality/unmapped_routes_{timestamp}.md（若 api_coverage_status=PARTIAL 必填；否则写 N/A）

### 3) 覆盖口径声明（必须保留）
- 若 coverage_mode=SAMPLE 或 api_coverage_status=PARTIAL：
  本报告仅代表“已映射入口”审计结论，不代表全量活动 API 结论。

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
最开始必须包含一张 Skill 使用与发现矩阵，覆盖所有已纳入本项目执行范围的 dotnet-* skills。

推荐字段：

| skill_name       | skill_type | execution_status | findings_status    | primary_outputs                        | depends_on                    | notes |
| ---------------- | ---------- | ---------------- | ------------------ | -------------------------------------- | ----------------------------- | ----- |
| dotnet-sql-audit | vuln_audit | COMPLETED        | FOUND / NO_FINDING | vuln_audit/sql_*.md; vuln_poc/sql_*.md | route_tracer; framework_audit | -     |

字段解释：

- skill_name：具体 Skill 名称
- skill_type：framework_audit / vuln_audit / route_tracer / mapping / dependency_scan 等
- execution_status：NOT_RUN / INITIAL_SCREENED / PARTIAL / COMPLETED / NOT_APPLICABLE
- findings_status：FOUND / NO_FINDING / PENDING_VERIFICATION / ENVIRONMENT_DEPENDENT
- primary_outputs：本 Skill 生成或主消费的文件
- depends_on：其依赖的前置阶段或关键产物
- notes：阻断原因、复核建议、环境限制、证据缺口

其中“其他漏洞类型”如果只是跑了抓手初筛，没有完成完整专项分析，必须明确标记为 INITIAL_SCREENED；如果已进入专项分析但未完成闭环，必须标记为 PARTIAL。

### 6) 漏洞列表总览
（引用 vuln_audit/* 与 vuln_poc/* 结论，参照漏洞详情模板填写漏洞详情）

### 7) Trace 未闭合 / 待补证风险池
（列出 route_id 或 SINK_ONLY 合成 ID、缺失证据与建议动作）
```

## 验收要点

- `api_coverage_status != COMPLETE` 时，`pipeline_execution` 禁止为 `COMPLETED`
- `coverage_mode = SAMPLE` 时，`pipeline_execution` 禁止为 `COMPLETED`
- `api_coverage_status = PARTIAL` 时，`unmapped_routes_source` 不得为 N/A，必须指向实际产物文件
- `exploit_chain_consistency_check_counts` 必须与 `exploit_chain` 总览表统计一致
- 若 `consistency_check_status=BLOCKED`，`quick_validation.final_decision` 必须联动为 `BLOCKED`
- 若存在 `final_anchor_checklist_{timestamp}.md`，建议最终报告回写其 `final_anchor_decision` 与 PASS/BLOCKED/PENDING 计数

## 最小示例（可复制）

```md
## 质量报告章节（固定）

### 1) 完成态双声明
- audit_surface_status: PARTIAL
- api_coverage_status: PARTIAL
- coverage_mode: SAMPLE

### 2) 覆盖门禁摘要
- api_coverage_percent: 88%
- pipeline_execution: PARTIAL
- gate_decision: FORCE_PARTIAL
- gate_reason: api_coverage_status=PARTIAL
- unmapped_routes_source: quality/unmapped_routes_2026_06_25_10_20.md
### 3) 覆盖口径声明（必须保留）
- 本报告仅代表“已映射入口”审计结论，不代表全量活动 API 结论。

### 4) exploit-chain 覆盖口径摘要（固定）
- exploit_chain_source: exploit_chain/exploit_chains_2026_06_25_10_20.md
- exploit_chain_coverage_mode: SAMPLE
- exploit_chain_api_coverage_status: PARTIAL
- exploit_chain_api_coverage_percent: 88%
- exploit_chain_sampled_scope: true

### 4.5) 一致性核对摘要（建议）
- consistency_check_source: quality/coverage_consistency_check_2026_06_25_10_20.md
- consistency_check_status: PASS
- exploit_chain_consistency_check_counts: {PASS:3, BLOCKED:0, N/A:1}

### 4.6) 收尾锚点检查结果引用（建议）
- final_anchor_checklist_source: quality/final_anchor_checklist_2026_06_25_10_20.md
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

### 1) 完成态双声明
- audit_surface_status: PARTIAL
- api_coverage_status: PARTIAL
- coverage_mode: SAMPLE

### 2) 覆盖门禁摘要
- api_coverage_percent: 88%
- pipeline_execution: PARTIAL
- gate_decision: FORCE_PARTIAL
- gate_reason: api_coverage_status=PARTIAL
- unmapped_routes_source: quality/unmapped_routes_2026_06_25_18_10.md
### 3) 覆盖口径声明（必须保留）
- 本报告仅代表“已映射入口”审计结论，不代表全量活动 API 结论。

### 4) exploit-chain 覆盖口径摘要（固定）
- exploit_chain_source: exploit_chain/exploit_chains_2026_06_25_18_10.md
- exploit_chain_coverage_mode: SAMPLE
- exploit_chain_api_coverage_status: PARTIAL
- exploit_chain_api_coverage_percent: 88%
- exploit_chain_sampled_scope: true

### 4.5) 一致性核对摘要（建议）
- consistency_check_source: quality/coverage_consistency_check_2026_06_25_18_10.md
- consistency_check_status: BLOCKED
- exploit_chain_consistency_check_counts: {PASS:3, BLOCKED:0, N/A:1}

### 4.6) 收尾锚点检查结果引用（建议）
- final_anchor_checklist_source: quality/final_anchor_checklist_2026_06_25_18_10.md
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


## 漏洞详情模板（强制使用）

> 在  **固定模板（强制字段）**的  **### 6) 漏洞列表总览** 中使用。

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
