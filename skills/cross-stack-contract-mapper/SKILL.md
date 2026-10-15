---
name: cross-stack-contract-mapper
description: 前后端跨端契约对账 Skill。将前端/BFF 出站调用与 dotnet 后端路由清单逐条对账，产出 matched / frontend_only / backend_only 三桶，其中 backend_only 作为隐藏攻击面直接写入高危入口池建议。
---

# Cross-Stack Contract Mapper

## 共享抓手索引引用

本 Skill 的枚举关键字、归一化规则与产物路径以 `skills/shared/IO_PATH_CONVENTION.md` 为单一真源，前端调用点抓手同时参考 `skills/shared/NODE_AUDIT_GRABBER_INDEX.md` 中跨端/HTTP 客户端相关章节。dotnet 侧路由消费格式遵循 `skills/dotnet-route-mapper/SKILL.md` 输出的 `route_mapping/routes_{timestamp}.md`，参数结构消费 `route_mapping/params_{timestamp}.md`。

## 输入依赖

- `dotnet_source_path` 与 `dotnet/route_mapping/routes_{timestamp}.md`：dotnet 侧已映射路由清单（必需）。
- `node_source_path`：前端/BFF 源码根目录（必需）。
- `dotnet/route_mapping/params_{timestamp}.md`：dotnet 侧参数结构（参数级对账必需）。
- `node/stack_detect/stack_detect_{timestamp}.md`：阶段 0 技术栈检出，用于选择框架特定调用模式（推荐）。
- `context_path` / baseURL 环境变量名：反向代理、网关前缀、Next.js basePath、vite/webpack devServer proxy 前缀等（可选，必须有配置或代码证据来源）。

## 前端调用点枚举（强制细化）

在前端/BFF 源码中逐条定位所有出站 HTTP 调用，禁止静默丢弃。优先抓手如下：

| 类别 | 优先关键字 / 模式 | 记录要求 |
| ---- | ---- | ---- |
| 通用 HTTP 客户端 | `axios.`、`fetch(`、`$fetch`、`useFetch`、`got(`、`request(` | 方法、URL 模板或调用串、来源文件位置 |
| 项目封装 | `apiClient`、`request` 等内部封装（按实际命名） | 追踪封装内部 baseURL 与最终请求拼接 |
| Next.js 特定 | `rewrites()`、`middleware.ts` 重写目标 | 记录重写后的真实目标路径 |
| 代理中间件 | `http-proxy-middleware`、vite/webpack `devServer.proxy` | 展开代理前缀与目标映射 |
| baseURL 环境变量 | `process.env.API_BASE_URL`、`import.meta.env.VITE_API_BASE_URL` 等 | 必须记录 baseURL 取值证据，用于后续拼接展开 |

枚举时必须同时记录：

- `call_id`：全局唯一调用点编号。
- `frontend_site`：调用点所在项目子目录/模块（如 `web/`、`bff/`、`admin/`）。
- `method`：HTTP 方法；动态方法必须标注 `DYNAMIC` 并列入未归一化清单。
- `raw_path`：源码中可见的 URL 模板或拼接片段。
- `base_url`：实际生效的 baseURL（含环境变量名与默认值）。
- `source_file:line`：调用点位置。

## 归一化规则（强制）

对每条前端调用构造对账键 `(HTTP_METHOD, normalized_path)`：

1. **baseURL 拼接展开**：将 `baseURL + url` 或模板前缀与路径片段拼接为完整路径；环境变量必须按实际取值或默认值展开，无法确定的标注 `base_url_unknown`。
2. **模板串取静态前缀**：对 `` `/api/users/${id}` ``、`` `/api/users/` + userId `` 等动态拼接，取可静态确定的路径前缀 `/api/users/`；纯动态路径（如变量整体作为路径）无法归一化的，列入「未归一化清单」。
3. **路径参数归一**：将 `:id`、`:name`、`[id]`、`*`、`{id}` 等路径参数占位统一替换为 `{param}`。
4. **方法归一**：HTTP 方法统一大写；无法静态确定的方法标注 `DYNAMIC` 并列入未归一化清单。
5. **尾部与查询串处理**：去除尾部斜杠差异（仅用于对账键比对，原始路径保留在 `notes`）；query 参数在 `normalized_path` 中只保留路径部分，query 字段名在参数级对账中处理。

## 三桶对账（强制）

以 `(HTTP_METHOD, normalized_path)` 为键，将前端调用与 dotnet `routes_{timestamp}.md` 中的 `route_method` + 归一化后 `route_path_template` 逐条比对，输出三桶：

| 桶 | 含义 | 下游动作 |
| ---- | ---- | ---- |
| `matched` | 前后端契约一致 | 进入参数级对账，并作为 `cross-stack-taint-linker` 输入池 |
| `frontend_only` | 前端存在调用，dotnet 后端无对应路由 | 幽灵调用线索；写入 `cross/api_contract_map_{timestamp}.md` 并标注可能原因（僵尸接口/版本漂移/网关代理/BFF 转发） |
| `backend_only` | dotnet 后端暴露路由，前端/BFF 未出现对应调用 | 隐藏攻击面；必须写入 `cross_analysis/high_risk_routes_{timestamp}.md`（或 `cross_analysis/sampled_high_risk_routes_{timestamp}.md`）建议，优先进入 dotnet 侧 route-tracer |

**frontend_only 后续动作（强制）**：对每条 frontend_only 记录按可能原因分类并给出处置动作——僵尸接口：核对近期 git log 确认删除或保留并记录决策；版本漂移：核对前端与后端发布版本，升级对齐或记录基线差异；网关代理：核对外部网关路由表，确认是否由网关消费；BFF 转发：核对 BFF 层转发目标，确认链路完整性。分类与动作必须写入 `cross/api_contract_map_{timestamp}.md` 的 notes 列。

`api_contract_map` 表头固定：

| call_id | method | normalized_path | frontend_site | matched_route_id | bucket | param_diff | notes |

- `matched_route_id`：匹配到的 dotnet `route_id`；`frontend_only` 写 `N/A`。
- `param_diff`：见下节，对 `frontend_only` 可写 `N/A`。
- `notes`：未归一化原因、baseURL 证据、幽灵调用推断、隐藏攻击面标注等。

## 参数级对账

对 `matched` 记录执行第二遍对账：对比前端调用实际发送的 query/body 字段名集合与 dotnet 侧 `params_{timestamp}.md` 中该 route_id 声明接受的参数集合。

- 将「后端接受但前端永不传」的字段写入 `param_diff` 小节。
- 将「前端传但后端未声明」的字段作为潜在隐藏参数 / Mass Assignment / 版本漂移线索写入 `notes`。
- 对字段名映射差异（如前端 `userId` 后端 `user_id`）在 `notes` 中标注。

`param_diff` 输出格式示例：

```md
- param_diff:
  - backend_only_params: [field_a, field_b]
  - frontend_only_params: [field_x]
  - mapping_mismatch: [{frontend: userId, backend: user_id}]
```

## 覆盖门禁（强制）

必须落盘 `cross/contract_coverage_gate_{timestamp}.md`，至少包含：

- 三桶计数：`matched_count`、`frontend_only_count`、`backend_only_count`。三桶分母一律取 `method_path_count`（(method,path) 展开口径）；消费 `unique_path_count` 属口径违规。
- 未归一化调用点清单：`unnormalized_calls`；动态拼接无法归一化的调用点必须列入，禁止静默丢弃。
- 契约覆盖率：

```
contract_coverage_percent = matched / (matched + frontend_only + backend_only)
```

- `unnormalized_rate`：`unnormalized_calls 数量 / 前端出站调用总数 × 100%`；> 10% 时 `contract_coverage_status` 强制 `PARTIAL`（覆盖率统计口径失真，必须声明为条件值）。
- `contract_coverage_status`：`COMPLETE` / `PARTIAL`。
- 分栈声明：若 `dotnet_api_coverage_status=PARTIAL` 或 `node_api_coverage_status=PARTIAL`，其 `matched` 率结论必须标注「受该栈 PARTIAL 影响，契约覆盖率为条件值」。
- `cross_analysis/high_risk_routes_source`：`backend_only` 写入高危入口池的来源文件路径。
- `params_{timestamp}.md` 缺失时：参数级对账无法执行，`contract_coverage_status` 降级并标注 `audit_side_missing=dotnet_params`（或 `=node_params`），matched 记录仅保留路径级结论。
- `pipeline_execution_allowed_completed`：仅当 `contract_coverage_status=COMPLETE` 且双栈 `api_coverage_status`（即 `dotnet_api_coverage_status` 与 `node_api_coverage_status`，对应各栈 `quality/api_coverage_gate_{timestamp}.md`）均不为 PARTIAL（或用户显式接受）时允许 `true`。

## 输出

按 `skills/shared/IO_PATH_CONVENTION.md` 中跨端产物路径落盘：

| 产物 | 物理路径 |
| ---- | ---- |
| 契约对账三桶表 | `cross/api_contract_map_{timestamp}.md` |
| 契约覆盖门禁 | `cross/contract_coverage_gate_{timestamp}.md` |
| 阶段索引 | `cross_analysis/index_{timestamp}.md`（记录 cross-stack-contract-mapper 执行状态与产物清单） |
| 空结果说明 | `cross_analysis/empty_result_{timestamp}.md`（无有效调用点或单栈模式时） |

`cross/api_contract_map_{timestamp}.md` 必须包含：

- 对账范围说明（dotnet routes 时间戳、node 源码范围、baseURL 证据）。
- `api_contract_map` 总表（表头固定）。
- 按 `bucket` 分桶的小节：`matched`、`frontend_only`、`backend_only`。
- `param_diff` 小节（汇总 matched 记录的参数差异）。
- `unnormalized_calls` 小节。
- 结论与下一步动作（进入 `cross-stack-taint-linker`、`backend_only` 高危入口池建议）。
