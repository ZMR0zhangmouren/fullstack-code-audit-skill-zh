# .NET Route / Trace 输出模板

本文件统一 dotnet-route-mapper 与 dotnet-route-tracer 的产物格式，用于减少不同 Skill、不同批次分析之间的格式漂移。

## 使用规则

- route-mapper 与 route-tracer 的输出结构以本文件为准
- 具体字段可以按专项补充，但不得删除本文件定义的核心章节与关键字段
- 若项目需要额外字段，应在保持兼容的前提下附加，不要修改既有主键语义
- routes_{timestamp}.md 中的 route_id、params_{timestamp}.md 中的路由条目、trace_{timestamp}.md 中的 route_id 必须一致

## 一、route-mapper 输出模板

### 0. controller_inventory_{timestamp}.md（门禁前置）

最小章节：

- 标题
- 生成时间
- 分析路径
- 控制器对账表
- 未映射控制器与原因

每条控制器最少字段：

- controller_name
- controller_file
- route_prefix
- action_count
- mapped_actions
- in_route_mapping（是/否）
- in_auth_mapping（是/否）
- unmapped_reason

参考骨架：

```md
# {project_name} - Controller Inventory
生成时间: {timestamp}
分析路径: {source_path}

## 控制器对账表
| controller_name | controller_file | route_prefix | action_count | mapped_actions | in_route_mapping | in_auth_mapping | unmapped_reason |
|---|---|---|---:|---:|---|---|---|

## 未映射控制器与原因
- ...
```

### 1. routes_{timestamp}.md

最小章节：

- 标题
- 生成时间
- 分析路径
- 路由清单（全部）
- 计数对账（强制）

每条路由最少字段：

- route_id
- 入口类型
- HTTP 方法或操作名
- 路由路径规则
- 路由声明方式
- Controller / Action 或等价处理器标识
- 处理器
- 位置
- 版本
- Area
- 参数概览
- 返回模板类型

参考骨架：

```md
# {project_name} - 路由与入口索引（.NET）
生成时间: {timestamp}
分析路径: {source_path}

## 路由清单（全部）
=== [1] GET /api/v{version}/users/{id} ===
入口类型: HTTP
HTTP 方法: GET
路由路径规则: /api/v{version}/users/{id}
路由声明方式: Attribute Routing
Controller: UsersController
Action: GetById
处理器: UsersController.GetById
位置: Controllers/UsersController.cs:line
版本: v{version}
Area: 无
参数概览:
  Path: id, version
  Query: includeRoles
  Header: X-Tenant-Id
返回模板类型: JsonResult
```

### 1.1 计数对账节（强制）

routes 文件头部在「分析路径」之后必须追加三行：

declared_route_count: {声明总数}
expanded_route_count: {展开明细总条数}
count_self_check: PASS | FAIL

并在文件末尾追加「计数对账」节，逐控制器列出算式（格式：控制器名: 展开数，最后 Σ 求和），
明确写出 `声明总数 = Σ 各控制器展开数 (+ 非控制器路由)` 的核算过程。
count_self_check=FAIL 时禁止交付给 route-tracer / 下游阶段，先修正计数再继续。

### 2. params_{timestamp}.md

最小章节：

- 标题
- 生成时间
- 按 route_id 或路由标题分段的参数详细

每条入口最少字段：

- Path 参数表
- Query 参数表
- Body / Form / Header / Cookie / File / Service / Custom Binder 参数表
- 完整请求模板

参考骨架：

````md
# {project_name} - 入口参数结构（逐条）
生成时间: {timestamp}

=== 路由: GET /api/v{version}/users/{id} ===
1) Path 参数
| 参数 | 类型/约束 | 来源 | 必填 | 说明 |
|------|-----------|------|------|------|
| id | int | [FromRoute] / route template | 是 | 用户 ID |

2) Query 参数
| 参数 | 类型 | 来源 | 必填 | 说明 |
|------|------|------|------|------|
| includeRoles | bool | [FromQuery] | 否 | 是否包含角色 |

5) 完整请求模板
```http
GET /api/v1/users/123?includeRoles=true HTTP/1.1
Host: {host}
Authorization: Bearer {token}
X-Tenant-Id: {tenant}
Cookie: {cookie}
```
````

### 3. quality/route_mapper_validation_{timestamp}.md

最小章节：

- 覆盖统计
- 未确定方法或路径组合
- conventional / attribute 路由冲突提示
- 参数绑定不确定项
- 需要 route-tracer 进一步确认的入口清单

### 4. quality/api_coverage_gate_{timestamp}.md（强制）

最小章节：

- 覆盖统计
- 未映射控制器清单
- 未映射 action 清单
- coverage 结论与门禁结果

最少字段：

- active_controller_total
- mapped_controller_count
- mapped_action_count
- unique_path_count
- method_path_count
- unmapped_controllers
- unmapped_actions
- api_coverage_percent
- api_coverage_status（COMPLETE/PARTIAL）

参考骨架：

```md
# API Coverage Gate
生成时间: {timestamp}
coverage_mode: {FULL|SAMPLE}

## 覆盖统计
- active_controller_total: {n}
- mapped_controller_count: {n}
- mapped_action_count: {n}
- unique_path_count: {唯一路径数}
- method_path_count: {(method,path) 展开总数}
- api_coverage_percent: {n}%
- api_coverage_status: {COMPLETE|PARTIAL}

注：两字段与 routes 文件头部一致；契约对账唯一消费口径为 method_path_count。

## 未映射控制器清单
- ...

## 未映射 action 清单
- ...

## 门禁结果
- pipeline_execution_allowed_completed: {yes|no}
- reason: ...
```

### 4.5 quality/unmapped_routes_{timestamp}.md（`api_coverage_status=PARTIAL` 时强制）

用途：单独沉淀“未映射入口风险面”，防止被 gate 统计字段淹没。

最少字段：

- api_coverage_status
- unmapped_controller_count
- unmapped_action_count
- unmapped_controllers
- unmapped_actions
- next_backfill_batch

参考骨架：

```md
# Unmapped Routes Backlog
生成时间: {timestamp}
coverage_mode: {FULL|SAMPLE}
api_coverage_status: {COMPLETE|PARTIAL}

## 统计
- unmapped_controller_count: {n}
- unmapped_action_count: {n}

## 未映射控制器
- {ControllerName} | {file} | {reason}

## 未映射 Action
- {Controller}.{Action} | {method/path} | {reason}

## 下一轮补图批次建议
- batch_001: {controller/action 列表}
- batch_002: {controller/action 列表}
```

### 4.6 quality/route_mapping_backfill_loop_{timestamp}.md（建议）

用途：记录循环补图轮次，避免“发现高危后提前结束映射”。

最少字段：

- round
- mapped_controllers_delta
- mapped_actions_delta
- unmapped_remaining
- decision

参考骨架：

```md
# Route Mapping Backfill Loop
生成时间: {timestamp}

## Round 1
- mapped_controllers_delta: +8
- mapped_actions_delta: +42
- unmapped_remaining: 17
- decision: continue

## Round 2
- mapped_controllers_delta: +5
- mapped_actions_delta: +23
- unmapped_remaining: 12
- decision: continue

## Round N
- mapped_controllers_delta: +0
- mapped_actions_delta: +0
- unmapped_remaining: 0
- decision: stop (converged)
```

### 4.7 unmapped_routes 失败反例（BLOCKED）

用途：训练执行人识别“入口覆盖不完整且未完成补图”时，后续阶段不得被误写为可交付。

```md
# Unmapped Routes Backlog (Blocked)
生成时间: 2026_06_25_20_40
coverage_mode: FULL
api_coverage_status: PARTIAL

## 统计
- unmapped_controller_count: 2
- unmapped_action_count: 7

## 未映射控制器
- AdminController | Controllers/AdminController.cs | route mapping 未覆盖
- ExportController | Controllers/ExportController.cs | auth mapping 未闭合

## 未映射 Action
- AdminController.DeleteUser | DELETE /api/admin/users/{id} | 高权限入口未补图
- ExportController.ExportZip | POST /api/export/zip | FILE/WRITE 风险入口未补图

## 下一轮补图批次建议
- batch_001: AdminController.*
- batch_002: ExportController.ExportZip, ExportController.ExportCsv

## 阻断说明
- final_decision: BLOCKED
- reason: 活动 API 入口覆盖仍为 PARTIAL，且关键高风险控制器未完成补图。
```

## 二、route-tracer 输出模板

### 1. route_tracer/{route_id}/trace_{timestamp}.md

最小章节：

- 请求模板
- 入口与元数据
- 参数进入点
- 绑定链
- 过滤器与中间件
- 业务与 DI 链
- 分支路径追踪
- 参数可控性矩阵
- Sink 定位
- Sink Summary
- Trace 完整性声明
- Sink Evidence Type Checklist

参数可控性矩阵最少字段：

- 参数名
- 绑定源
- 转换器 / 绑定器
- 首次校验点
- 最终使用点
- 可控等级
- 受影响 Sink

Sink Summary 最少字段：

- Sink 类型
- 具体 API
- 代码位置
- 上游参数
- 是否经过编码 / 白名单 / 授权 / 配置保护
- 证据强度

参考骨架：

````md
# Route Trace - {route_id}
生成时间: {timestamp}
入口: GET /api/v1/users/123

## 请求模板
```http
GET /api/v1/users/123?includeRoles=true HTTP/1.1
Host: {host}
Authorization: Bearer {token}
```

## 入口与元数据
- Controller: UsersController
- Action: GetById
- Authorize: Policy=UserRead

## 参数进入点
- id <- Route
- includeRoles <- Query

## 绑定链
- [FromRoute] id -> int id

## 过滤器与中间件
- AuthorizationFilter: UserReadPolicy
- Middleware: UseAuthentication -> UseAuthorization

## 业务与 DI 链
- UsersController.GetById
- IUserService.GetById
- UserRepository.Load

## 参数可控性矩阵
| 参数名 | 绑定源 | 转换器/绑定器 | 首次校验点 | 最终使用点 | 可控等级 | 受影响 Sink |
|------|------|------|------|------|------|------|
| id | Route | 默认绑定 | GetById guard | SqlCommand parameter | 高 | SQL |

## Sink Summary
| Sink 类型 | API | 代码位置 | 上游参数 | 保护措施 | 证据强度 |
|------|------|------|------|------|------|
| SQL | SqlCommand.ExecuteReader | Repository/UserRepository.cs:line | id | 参数化 | COMPLETE |

## Trace 完整性声明
- trace_status: COMPLETE
- 说明: Controller / Binder / Filter / Middleware / DI / Sink 六层均已闭合

## Sink Evidence Type Checklist
- 以 dotnet-route-tracer/SKILL.md 的 ## 9) 为单一真源（本文件不重复维护 EVID_* 行表，避免两处漂移）
- 本章节标题与表头必须存在；实际命中 Sink 的证据行从 tracer checklist 对应行复制

## 新增：taint_nodes（关键数据角色分步记录）

对每个追踪的链路，必须分节点记录，将"模型可以糊弄过去的思考"变成"必须交代的结构"。

### taint_nodes 字段定义

| 节点类型 | 说明 | 必填字段 |
|---------|------|---------|
| `source_write_entry` | 写入入口：危险数据从哪里来、是否受攻击者控制 | filepath, line_range, description, is_attacker_controllable |
| `source_trigger_entry` | 触发入口：什么时候读取、谁触发 | filepath, line_range, description, trigger_condition |
| `storage_read` | 持久化读取（数据库/缓存/文件/Session） | filepath, line_range, description |
| `transfer` | 传播节点（赋值/传递/拼接/转换） | filepath, line_range, description |
| `barrier` | 安全控制点 | line_range, barrier_type, actual_behavior, status(PASSED/FAILED/NOT_ANALYZED) |
| `sink` | 最终执行点 | filepath, line_range, description |

### taint_nodes 示例

```json
{
  "taint_nodes": [
    {
      "taint_type": "source_write_entry",
      "filepath": "Controllers/ConfigController.cs",
      "line_range": "45-48",
      "description": "用户通过 SaveFieldConfig 接口写入 column_key，需业务配置管理员权限",
      "is_attacker_controllable": true
    },
    {
      "taint_type": "storage_read",
      "filepath": "Services/SearchService.cs",
      "line_range": "30-33",
      "description": "从 field_config 表读取 column_key"
    },
    {
      "taint_type": "transfer",
      "filepath": "Services/SearchService.cs",
      "line_range": "40-44",
      "description": "column_key 被拼入 SQL 查询条件"
    },
    {
      "taint_type": "barrier",
      "line_range": "40-44",
      "barrier_type": "column_whitelist",
      "actual_behavior": "无白名单校验，column_key 直接进入列标识符位置",
      "status": "FAILED"
    },
    {
      "taint_type": "sink",
      "filepath": "Services/SearchService.cs",
      "line_range": "45-48",
      "description": "SQL 执行：column_key 进入列标识符位置"
    }
  ]
}
```

### taint_nodes 验收标准

- [ ] 每个追踪链路都有 taint_nodes 记录
- [ ] source_write_entry 和 source_trigger_entry 已区分（二阶场景）
- [ ] 每个 barrier 都有 actual_behavior 和 status
- [ ] status 只能是 PASSED / FAILED / NOT_ANALYZED，不能省略
- [ ] 节点之间形成完整链：source → [storage_read] → transfer → [barrier] → sink

### 与现有字段的关系

- `taint_nodes` 是对 "参数可控性矩阵" 和 "Sink Summary" 的结构化补充
- "参数可控性矩阵" 回答"参数从哪来、可控等级如何"
- `taint_nodes` 回答"数据在链路中扮演什么角色、每个角色的证据是什么"
- 两者都必须在 trace 中存在，互相补充
````

### 2. route_tracer/{route_id}/trace_summary_{timestamp}.md

适用于批量分析时的轻量索引，最小字段：

- route_id
- 入口标识
- trace_status
- 关键 Sink 类型
- 关键未闭合点
- 建议交给的漏洞专项

## 三、字段一致性要求

- route_id 在 routes、params、trace、trace_summary、最终报告中必须保持同一标识
- 返回模板类型、入口类型、处理器标识在 route-mapper 与 route-tracer 中必须语义一致
- trace_status 仅允许 COMPLETE、PARTIAL、UNRESOLVED 三种值
- Sink 类型命名应与 shared/DOTNET_SINK_REFERENCE.md 和具体 vuln_audit 使用的分类保持一致

## 四、high risk routes 输出约束（覆盖模式）

- 当 `coverage_mode=FULL` 且 `api_coverage_status=COMPLETE` 时，输出 `cross_analysis/high_risk_routes_{timestamp}.md`
- 当 `coverage_mode=SAMPLE` 或 `api_coverage_status=PARTIAL` 时，输出 `cross_analysis/sampled_high_risk_routes_{timestamp}.md`
- sampled 文件头必须包含：
  - `coverage_mode`
  - `api_coverage_status`
  - `controller_coverage_percent`
  - `auth_coverage_percent`
  - `disclaimer`（明确声明“仅反映当前已映射入口中的高危候选，不代表全量活动 API 高危入口全集”）

### trace_batch_plan_{timestamp}.md 约束（覆盖模式绑定）

- `coverage_mode=FULL`：
  - `trace_batch_max_size` 允许区间：10–30
  - 默认值：10
  - 建议批次数提醒阈值：若 `planned_batch_count > 20`，建议评估是否合并批次（软约束，不强制回退）
- `coverage_mode=SAMPLE`：
  - `trace_batch_max_size` 允许区间：5–10
  - 默认值：8
  - 禁止超过 10
  - `batch_count_upper_bound` 固定为 6（计划总批次数不得超过 6）
- 每一批必须带字段：
  - `batch_id`
  - `coverage_mode`
  - `trace_batch_max_size`
  - `reason`
  - `route_ids`
- **单写者原则（2026-09-20，强制）**：trace_batch_plan / trace 索引类文件只允许编排层或指定单一批次写者写入，禁止多批次并发直写同一文件；并发场景必须分片命名 `trace_batch_plan_{批次}.md`，收尾合并归编排层负责，合并后正式产物名统一为 `trace_batch_plan_{timestamp}.md`

参考骨架：

```md
# Trace Batch Plan
生成时间: {timestamp}
coverage_mode: {FULL|SAMPLE}
batch_count_upper_bound: {6|N/A}
planned_batch_count: {n}

## 批次列表
### batch_001
- coverage_mode: SAMPLE
- trace_batch_max_size: 8
- reason: 样本模式下优先控制批次规模，降低上下文丢失与漏判风险
- route_ids:
  - HTTP:GET:/api/users/{id}
  - HTTP:POST:/api/orders/export
```

## 五、最小示例产物包（新增，回归对齐用）

用途：用于快速校验“覆盖门禁语义是否按统一口径落地”。

建议目录：`quality/minimal_sample_pack_{timestamp}/`

应至少包含以下 3 个示例文件：

1. `route_mapping/controller_inventory_{timestamp}.md`
2. `quality/api_coverage_gate_{timestamp}.md`
3. `cross_analysis/sampled_high_risk_routes_{timestamp}.md`

### 示例 A：controller_inventory_{timestamp}.md

```md
# DemoProject - Controller Inventory
生成时间: 2026_06_24_10_30
分析路径: /repo/demo

## 控制器对账表
| controller_name | controller_file | route_prefix | action_count | mapped_actions | in_route_mapping | in_auth_mapping | unmapped_reason |
|---|---|---|---:|---:|---|---|---|
| UsersController | Controllers/UsersController.cs | /api/users | 6 | 6 | 是 | 是 | |
| OrdersController | Controllers/OrdersController.cs | /api/orders | 5 | 4 | 是 | 否 | auth mapping 待补齐 |

## 未映射控制器与原因
- 无
```

### 示例 B：quality/api_coverage_gate_{timestamp}.md

```md
# API Coverage Gate
生成时间: 2026_06_24_10_30
coverage_mode: SAMPLE

## 覆盖统计
- active_controller_total: 2
- mapped_controller_count: 2
- mapped_action_count: 10
- api_coverage_percent: 90%
- api_coverage_status: PARTIAL

## 未映射控制器清单
- 无

## 未映射 action 清单
- OrdersController.ExportCsv

## 门禁结果
- pipeline_execution_allowed_completed: no
- reason: api_coverage_status=PARTIAL
```

### 示例 C：cross_analysis/sampled_high_risk_routes_{timestamp}.md

```md
# Sampled High Risk Routes
生成时间: 2026_06_24_10_30
coverage_mode: SAMPLE
api_coverage_status: PARTIAL
controller_coverage_percent: 100%
auth_coverage_percent: 80%
disclaimer: 仅反映当前已映射入口中的高危候选，不代表全量活动 API 高危入口全集。

## 路由候选
| route_id | method | path | source_bucket | reason |
|---|---|---|---|---|
| HTTP:GET:/api/users/{id} | GET | /api/users/{id} | P1 | 鉴权粒度不足（潜在 IDOR） |
| HTTP:POST:/api/orders/export | POST | /api/orders/export | SINK_SUSPECT | FILE/WRITE 相关参数可控 |
```

验收要点：

- 三个文件的 `timestamp` 应一致
- sampled 文件必须带 `disclaimer`
- gate 与 sampled 的 `api_coverage_status` 必须一致

## 六、quick_validation_{timestamp}.md（收尾校验模板）

用途：在交付前快速验证“门禁状态、产物完整性、报告声明”三者一致。

建议路径：`quality/quick_validation_{timestamp}.md`

最小字段：

- timestamp
- coverage_mode
- api_coverage_status
- pipeline_execution
- checklist_results
- final_decision

参考骨架：

```md
# Quick Validation
生成时间: 2026_06_24_11_15

## 运行上下文
- coverage_mode: SAMPLE
- api_coverage_status: PARTIAL
- pipeline_execution: PARTIAL

## 校验清单
- [x] route_mapping/controller_inventory_{timestamp}.md 存在
- [x] quality/api_coverage_gate_{timestamp}.md 存在
- [x] cross_analysis/sampled_high_risk_routes_{timestamp}.md 存在（SAMPLE/PARTIAL）
- [x] cross_analysis/trace_batch_plan_{timestamp}.md 在 SAMPLE 下满足 `planned_batch_count <= 6`
- [x] quality/pipeline_execution_{timestamp}.md 与 gate 状态一致
- [x] 最终报告包含双完成态声明
- [x] 最终报告包含覆盖口径声明
- [x] 最终报告包含 exploit-chain 覆盖口径摘要，且与 `exploit_chain/exploit_chains_{timestamp}.md` 一致
- [x] （建议）quality/coverage_consistency_check_{timestamp}.md 已落盘，且无冲突阻断项

## 字段冲突定位（如 coverage_consistency_check 存在）
- consistency_check_status: PASS
- conflicts_count: 0
- 冲突摘要: 无（若有冲突，写明"冲突字段 | 来源文件 | 修复建议"）

## 结论
- final_decision: PASS
- notes: 无阻断项，可交付
```

判定规则：

- 只要出现状态冲突（例如 `api_coverage_status=PARTIAL` 但 `pipeline_execution=COMPLETED`），`final_decision` 必须为 `BLOCKED`
- SAMPLE 模式下若缺少覆盖口径声明，`final_decision` 必须为 `BLOCKED`
- 若 `consistency_check_status=BLOCKED`，`final_decision` 必须为 `BLOCKED`

## 七、quick_validation_example_{timestamp}.md（最小示例）

用途：给首次接手者提供“可直接复制”的 quick validation 落盘样例。

建议路径：`quality/quick_validation_example_{timestamp}.md`

参考骨架：

```md
# Quick Validation Example
生成时间: 2026_06_24_12_10

## 运行上下文
- coverage_mode: SAMPLE
- api_coverage_status: PARTIAL
- api_coverage_percent: 88%
- pipeline_execution: PARTIAL

## 校验清单
- [x] route_mapping/controller_inventory_2026_06_24_12_10.md 存在
- [x] quality/api_coverage_gate_2026_06_24_12_10.md 存在
- [x] cross_analysis/sampled_high_risk_routes_2026_06_24_12_10.md 存在
- [x] cross_analysis/trace_batch_plan_2026_06_24_12_10.md 满足 SAMPLE 阈值（5–10）
- [x] cross_analysis/trace_batch_plan_2026_06_24_12_10.md 满足 SAMPLE 批次数上限（planned_batch_count <= 6）
- [x] exploit_chain/exploit_chains_2026_06_24_12_10.md 已透传覆盖口径
- [x] 最终报告已声明“仅覆盖已映射入口样本范围”
- [x] 最终报告已写入 exploit-chain 覆盖口径摘要，字段与 exploit_chain 文件一致
- [x] quality/coverage_consistency_check_2026_06_24_12_10.md 已核对关键字段一致，无阻断冲突

## 结论
- final_decision: PASS
- notes: SAMPLE 模式校验通过，可作为阶段性交付。
```

使用要求：

- `quick_validation_example` 用于示例与培训，不替代 `quick_validation` 正式产物
- 示例中的时间戳与文件名可按实际执行替换，但字段结构不得删减

### quick_validation 失败反例（计数对账失败，BLOCKED）

用途：训练执行人识别“状态看似一致但计数不一致”的阻断场景。

```md
# Quick Validation Example (Blocked)
生成时间: 2026_06_25_16_40

## 运行上下文
- coverage_mode: SAMPLE
- api_coverage_status: PARTIAL
- pipeline_execution: PARTIAL

## 校验清单
- [x] quality/coverage_consistency_check_2026_06_25_16_40.md 已落盘
- [ ] 最终报告 `exploit_chain_consistency_check_counts` 与 exploit_chain 总览表一致（失败）

## 字段冲突定位（如 coverage_consistency_check 存在）
- consistency_check_status: BLOCKED
- conflicts_count: 1
- 冲突摘要: exploit_chain_consistency_check_counts.BLOCKED | final_report vs exploit_chain/exploit_chains_2026_06_25_16_40.md | 重新统计并回写最终报告

## 结论
- final_decision: BLOCKED
- notes: 计数对账失败，禁止交付。
```

## 八、coverage_consistency_check_{timestamp}.md（跨产物一致性核对）

**双栈同构（强制）**：dotnet（`quality/coverage_consistency_check_{timestamp}.md`）与 node（`node/quality/coverage_consistency_check_{timestamp}.md`）必须产出同名独立文件，结构以本节为准。如确需归并到其他 quality 文件，归并文件必须包含标记行 `MERGED_FROM: coverage_consistency_check_{timestamp}.md` 与 `MERGE_REASON: {归并原因}`，且被归并文件路径仍须在 manifest 中登记；无独立文件且无标记行视为产物缺失。

用途：对 gate/trace/exploit-chain/final report 的关键字段做统一核对，定位冲突来源并给出修复建议。

建议路径：`quality/coverage_consistency_check_{timestamp}.md`

最小字段：

- timestamp
- compared_files
- consistency_matrix
- conflicts
- final_status

参考骨架：

```md
# Coverage Consistency Check
生成时间: 2026_06_24_14_20

## 对比文件
- quality/api_coverage_gate_2026_06_24_14_20.md
- cross_analysis/trace_batch_plan_2026_06_24_14_20.md
- exploit_chain/exploit_chains_2026_06_24_14_20.md
- DemoProject_代码审计_2026_06_24_14_20.md

## 一致性矩阵
| 字段 | gate | trace_batch_plan | exploit_chain | final_report | 一致性 |
|---|---|---|---|---|---|
| coverage_mode | SAMPLE | SAMPLE | SAMPLE | SAMPLE | PASS |
| api_coverage_status | PARTIAL | N/A | PARTIAL | PARTIAL | PASS |
| api_coverage_percent | 88% | N/A | 88% | 88% | PASS |
| planned_batch_count | N/A | 5 | N/A | 5 | PASS |
| exploit_chain_sampled_scope | N/A | N/A | true | true | PASS |

## 冲突项（如有）
- 无

## 结论
- final_status: PASS
- notes: 关键字段一致，可交付。
```

判定规则：

- 任一关键字段冲突且影响结论语义时，`final_status` 必须为 `BLOCKED`
- `final_status=BLOCKED` 时，必须给出“冲突字段 + 来源文件 + 修复建议”三元组

收尾核对清单（建议逐项勾选）：

- [ ] skill 清单计数核对：README/CLAUDE.md 中声明的 skill 数量与 `skills/` 磁盘实际数量一致（dotnet 与 node 家族分别核对）
- 字段对账静态映射以 IO_PATH_CONVENTION.md 的『收尾字段对账静态映射模板』为真源

## 九、最终报告固定模板（已抽离）

为减少多处维护导致的字段漂移，最终报告固定片段已抽离至：

- `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md`

使用约束：

- 最终报告质量章节必须以该文件为单一真源（Single Source of Truth）
- 若模板字段发生变更，先更新该文件，再同步消费方（pipeline/README/CLAUDE）

快速验收：

- `exploit_chain_consistency_check_counts` 的 PASS/BLOCKED/N/A 必须与 `exploit_chain` 总览表统计一致
- 若 `consistency_check_status=BLOCKED`，`quick_validation.final_decision` 必须联动为 `BLOCKED`

## 十、exploit-chain BLOCKED 失败反例（计数对账失败）

用途：训练执行人识别“利用链文件本身也需要降级措辞，而不是只修最终报告”的场景。

```md
# Exploit Chains Example (Blocked)
生成时间: 2026_06_25_19_20
coverage_mode: SAMPLE
api_coverage_status: PARTIAL
api_coverage_percent: 88%

## 链路总览表
| 链路编号 | 起点入口 | 终点目标 | 步骤数 | 最低权限 | 整体复杂度 | 可行性 | 瓶颈节点 | coverage_mode | api_coverage_status | sampled_scope | consistency_check_status |
|---|---|---|---:|---|---|---|---|---|---|---|---|
| CHAIN-001 | GET /api/users/{id} | Admin Token 泄露 | 2 | 无需认证 | 中 | 推断可行 | AUTH-002 | SAMPLE | PARTIAL | true | BLOCKED |

## consistency_check 计数统计
- consistency_check_counts: {PASS:0, BLOCKED:1, N/A:0}

## 链路详情
- consistency_check_source: quality/coverage_consistency_check_2026_06_25_19_20.md
- consistency_check_status: BLOCKED
- 降级声明: 当前链路因 consistency 计数对账失败已降级，暂不提供“确认可行”判定。
- 修复建议: 先修复 final_report 与 exploit_chain 总览表计数差异，再按 `final_report -> consistency_check -> quick_validation -> exploit_chain` 顺序重跑。
```

## 十一、final_anchor_checklist_{timestamp}.md（最小示例）

用途：给收尾阶段提供“逐文件勾选 + 汇总判定 + 阻断来源定位”的可复制样例。

建议路径：`quality/final_anchor_checklist_{timestamp}.md`

### final_anchor PASS 最小示例

```md
# Final Anchor Checklist
生成时间: 2026_06_25_21_10

- [x] 1. `quality/api_coverage_gate_2026_06_25_21_10.md` 已存在且 `api_coverage_status` 已确认
- [x] 2. `quality/coverage_consistency_check_2026_06_25_21_10.md` 已存在且 `final_status` 已确认
- [x] 3. `quality/quick_validation_2026_06_25_21_10.md` 已存在且 `final_decision` 已确认
- [x] 4. `exploit_chain/exploit_chains_2026_06_25_21_10.md` 已存在且链路可行性措辞已复核
- [x] 5. `DemoProject_代码审计_2026_06_25_21_10.md` 已回写最终结论与 consistency 计数

## 汇总
- checklist_pass_count: 5
- checklist_blocked_count: 0
- checklist_pending_count: 0
- final_anchor_decision: PASS
- pool_check: PASS
- stat_check: PASS
- chain_check: PASS

## BLOCKED 来源文件摘要（如有）
- 无
```

### final_anchor BLOCKED 最小示例

```md
# Final Anchor Checklist
生成时间: 2026_06_25_21_30

- [x] 1. `quality/api_coverage_gate_2026_06_25_21_30.md` 已存在且 `api_coverage_status` 已确认
- [x] 2. `quality/coverage_consistency_check_2026_06_25_21_30.md` 已存在且 `final_status` 已确认
- [ ] 3. `quality/quick_validation_2026_06_25_21_30.md` 已存在且 `final_decision` 已确认（失败）
- [x] 4. `exploit_chain/exploit_chains_2026_06_25_21_30.md` 已存在且链路可行性措辞已复核
- [ ] 5. `DemoProject_代码审计_2026_06_25_21_30.md` 已回写最终结论与 consistency 计数（失败）

## 汇总
- checklist_pass_count: 3
- checklist_blocked_count: 2
- checklist_pending_count: 0
- final_anchor_decision: BLOCKED
- pool_check: PASS
- stat_check: FAIL
- chain_check: FAIL

## BLOCKED 来源文件摘要（如有）
- quality/quick_validation_2026_06_25_21_30.md | final_decision | consistency_check_status=BLOCKED
- DemoProject_代码审计_2026_06_25_21_30.md | exploit_chain_consistency_check_counts | 与 exploit_chain 总览表统计不一致
```

使用要求：

- 若 `checklist_blocked_count > 0`，`final_anchor_decision` 必须为 `BLOCKED`
- 若存在 `quality/final_anchor_checklist_{timestamp}.md`，最终报告 `4.6` 字段必须与其汇总区块一致
- 若 `final_anchor_decision=BLOCKED`，最终报告不得写“可交付/已通过/收尾完成”

### 机器校验（计数=枚举数，2026-09-20）

收尾时除人工逐行勾选外，必须执行以下三行机器校验并记录结果（公式口径以 `IO_PATH_CONVENTION.md` 待补证风险池节「计数三公式」为唯一真源；三行结果分别以 `pool_check` / `stat_check` / `chain_check` 字段记入上方汇总区块，取值 PASS/FAIL）：

- [ ] 池计数=唯一 id 数：`pending_pool_{timestamp}.md` 的 `pool_total` 等于按 pool_id 去重后的行数（一 id 一行，无别名合并行；状态分桶之和 = pool_total）
- [ ] 发现统计表=详情块枚举数：各产物「发现统计表」表内计数等于对应详情块实际枚举条目数，逐条点名可回溯
- [ ] 链状态分解自洽：exploit_chain 链路状态分解满足 `closed + open + 误报 = 总链数`（closed = 非误报非 pending 之和）；不满足时 `final_anchor_decision` 必须为 `BLOCKED`

## 未覆盖攻击面风险摘要（PARTIAL/SAMPLE 强制）

| 可达性 \ 敏感操作 | 读写 | 管理 | 资金/数据导出 | 合计 |
| ---- | ---- | ---- | ---- | ---- |
| 匿名可达 | {n} | {n} | {n} | {n} |
| 认证可达 | {n} | {n} | {n} | {n} |
| 内网/角色可达 | {n} | {n} | {n} | {n} |

- 未覆盖入口清单摘要：{Top N 路由/方法/路径}
- 残余风险区间：{按 SEVERITY_RATING 分级的最高可能等级与依据}
- 建议：{补图批次或接受声明的理由}
