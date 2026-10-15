---
name: cross-stack-taint-linker
description: 跨端污点链拼接 Skill。以 contract-mapper 的 matched 记录为链起点池，将 node 侧入口到出站调用的污点流与 dotnet 侧 route-tracer 证据拼接为跨端正向/反向链，受 trace-gate 双证据约束，未闭合链进风险池。
---

# Cross-Stack Taint Linker

## 共享抓手索引引用

本 Skill 的产物路径以 `skills/shared/IO_PATH_CONVENTION.md` 为单一真源（`cross_taint_links_{timestamp}.md` 已登记于 :252）。node 侧出站调用点抓手参考 `skills/shared/NODE_AUDIT_GRABBER_INDEX.md` 中 HTTP 客户端相关章节；证据点引用以 `skills/shared/EVIDENCE_POINT_IDS.md` 为口径（node 侧 `EVID_NODE_*`、dotnet 侧既有 `EVID_*`）。前端渲染 sink 与 dotnet 响应字段的证据消费格式遵循对应漏洞专项（node 侧 `node-xss-audit`、dotnet 侧 `dotnet-xss-audit/SKILL.md`）输出。

## 输入依赖

| 输入 | 路径 | 必需性 |
| ---- | ---- | ---- |
| 契约对账三桶表 | `{output_root}/cross/api_contract_map_{timestamp}.md` | **必需**，`matched` 记录为链起点池 |
| node 侧 route-tracer 产物 | `{output_root}/node/route_tracer/` 各 trace 产物 | 按链需求读取（闭合链必须存在） |
| dotnet 侧 route-tracer 产物 | `{output_root}/dotnet/route_tracer/` 各 trace 产物 | 按链需求读取（闭合链必须存在） |
| node 侧出站调用点清单 | route-tracer 汇总或本 Skill 枚举 `axios` / `fetch(` / `got(` 等出站调用 | 必需（正向链定位） |
| 技术栈检出 | `{output_root}/node/stack_detect/stack_detect_{timestamp}.md` | 推荐（确定前端形态与 SSR 面） |

- 前置约束：`cross/api_contract_map_{timestamp}.md` 不存在或 `matched_count=0` 时，本 Skill 降级为仅执行反向链（dotnet 响应 → 前端渲染 sink 不需契约记录），并在产物中声明 `forward_chain_skipped=NO_MATCHED_RECORD`。
- 跨端链拼接依赖双栈 trace 时间戳：node 与 dotnet route-tracer 产物时间戳需与 contract_map 同一审计批次，批次不一致的链在 `missing_evidence` 中标注 `trace_batch_mismatch`。

## 正向链追踪（浏览器→BFF→dotnet sink）

正向链定义：**node source → BFF 内部传递 → 出站调用参数 →（经 contract_map matched 记录对齐）→ dotnet 对应 route 参数 → dotnet sink**，方向标注 `forward`。链式示意：

```
req.*（node source，用户可控）
  → BFF 内部传递（中间件/路由处理器/数据装配）
  → 出站调用参数（axios/fetch/got 请求体或 query）
  → contract_map matched 记录（(METHOD, normalized_path) 对齐）
  → dotnet 对应 route 参数（route_id + 参数名对齐）
  → dotnet sink（SQL/命令/文件/反序列化等）
```

执行步骤（强制）：

1. **取链起点池**：从 `cross/api_contract_map_{timestamp}.md` 读取全部 `matched` 记录；`backend_only` 记录不在此池（其链属 dotnet 单栈 trace），`frontend_only` 记录作为「幽灵调用」另列备注，不参与拼接。
2. **定位出站调用点**：按 `call_id` 回到前端/BFF 源码，确认该调用点的实际请求体/query 是否含用户可控字段（`req.*` 或上游中间件注入数据）；枚举关键字 `axios.`、`fetch(`、`$fetch`、`got(`、`request(` 及项目封装。
3. **追 node 侧污点流**：node source → 出站调用参数的内部传递路径，形成 node 侧半链（引用 `node/route_tracer/` trace 产物或 `EVID_NODE_*` 证据，如 `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT`、`EVID_NODE_SESS_*` 等按污染类型取对应证据点）。
4. **对齐 contract 记录**：出站调用 `(METHOD, normalized_path)` 与该 matched 记录对账；记录行号/记录键作为 `contract_record` 引用（格式：`api_contract_map_{ts}.md 行号/记录`）。
5. **追 dotnet 侧半链**：从 matched 的 `matched_route_id` 出发，消费 `dotnet/route_tracer/` 中该 route 的 trace，确认参数到达 sink 的路径；无现成 trace 时引用 dotnet route-mapper 参数结构，标注 `dotnet_trace_pending`。
6. **编号与登记**：命中生成 `XTRACE-{n}` 跨端链 ID。编号独立从 `XTRACE-1` 起（contract-mapper 无全局链编号约定），正向/反向链共用同一编号序列；一链一 ID，禁止复用。

## 反向链追踪（dotnet 响应→前端渲染 sink）

反向链定义：**dotnet 响应字段（如用户可控字段透传）→ 前端渲染 sink → stored XSS 利用链主通道**，方向标注 `reverse`。链式示意：

```
dotnet 响应字段（如用户可控字段原样透传）
  → BFF 透传/包装（fetch 响应转发）
  → 前端渲染 sink
    ├── dangerouslySetInnerHTML
    ├── v-html
    └── SSR 注水（__NEXT_DATA__ / __NUXT__）
  → stored XSS 利用链主通道
```

执行步骤（强制）：

1. **定位透传响应字段**：从 dotnet 侧 route-tracer / XSS 专项产物中取「响应字段可控且未净化」的证据（引用 `EVID_XSS_*` 或 dotnet route-tracer 文件行号）。
2. **确认 BFF 透传形态**：BFF 是否原样转发响应体（不重编码、不净化）——引用 node 侧出站调用点与响应处理代码位置。
3. **定位前端渲染 sink**：`dangerouslySetInnerHTML` / `v-html` / SSR 注水（`__NEXT_DATA__` / `__NUXT__`）渲染该字段的位置，引用 `EVID_NODE_XSS_SSR_HYDRATION` 等证据；需结合 `node/stack_detect/stack_detect_{timestamp}.md` 确定是纯 SPA 还是 SSR 面。
4. **编号与登记**：命中生成 `XTRACE-{n}`，方向字段填 `reverse`，结论标注为 stored XSS 利用链主通道，供 `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` 消费。

## trace-gate 双证据约束（强制）

跨端高强度结论（闭合链）必须**同时**持有两侧证据，缺一不可：

| 证据侧 | 要求 | 可接受形式 |
| ---- | ---- | ---- |
| node 侧 | 必须存在 | `EVID_NODE_*` 证据点或 `node/route_tracer/` trace 文件引用（含文件路径与行号） |
| dotnet 侧 | 必须存在 | dotnet route-tracer trace 文件引用或既有 `EVID_*` 证据点（含文件路径与行号） |

约束规则（强制）：

- 仅单侧证据的链一律入**待补证风险池**，禁止静默删除（与漏报抑制原则一致）。
- 闭合状态仅允许标注：`closed`（双证据齐） / `pending`（缺证据）；`closed` 与 `误报（双端防护证据齐全 fail-close）` 是互斥的——有双端防护证据时走误报判定而非闭合。
- 引用证据必须真实存在：本 Skill 禁止引用未落盘的证据点；引用 `file:line` 需在交付前复核存在性。

## 判定规则

三态判定（对每条 XTRACE 链）：

| 结论 | 条件 |
| ---- | ---- |
| `已确认（双证据闭合）` | node 侧 trace 证据 + dotnet 侧 route-tracer 证据齐备，且 contract 记录精确 matched（`param_diff` 无前端字段缺失导致链断裂），双端防护证据均不存在 |
| `待验证（单侧证据或 contract 记录不精确）` | 仅单侧证据；或 contract 记录未 matched / 模糊对齐；或 trace_batch_mismatch |
| `误报（双端防护证据齐全 fail-close）` | 任一侧存在完整防护证据（参数化查询、编码净化、输出转义、严格校验等），链被 fail-close 阻断 |

判定顺序强制：先查防护（误报）→ 再查证据完整性（已确认/待验证）→ 其余入风险池。所有三态结论均需在产物中留痕，不得省略 `待验证` 链。

## 风险池与未闭合处理

- 未闭合链（`待验证`）写入 `cross/cross_taint_links_{timestamp}.md` 的 `open` 区段，与 `closed` 区段并列展示。
- 缺失证据清单逐条列出，分类枚举：
  - `missing_node_trace`：缺 node 侧 trace / 出站调用点证据。
  - `missing_dotnet_trace`：缺 dotnet 侧 route-tracer 证据。
  - `contract_record_unmatched`：contract 记录未 matched（含 `frontend_only` 幽灵调用与 `param_diff` 断裂）。
- open 区段链的下一步动作：补齐对应栈 route-tracer 后回滚重跑本 Skill；禁止删除。
- 全部链闭合但存在 `open` 链时，产物结论须声明 `trace_closure_status=PARTIAL`，不得写成全量闭合。

## 证据引用

本 Skill 直接引用的证据点（引用口径以 `skills/shared/EVIDENCE_POINT_IDS.md` 为准）：

| 证据点 | 用途 |
| ---- | ---- |
| `EVID_NODE_*`（如 `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT`、`EVID_NODE_SESS_*`） | node 侧污点传播 / 注入面证据 |
| dotnet 侧既有 `EVID_*`（如 `EVID_XSS_*`、`EVID_SQL_*` 等按 sink 类型） | dotnet 侧 sink 证据 |
| contract_map 记录行号 | `contract_record` 引用（`cross/api_contract_map_{timestamp}.md`） |
| `node/route_tracer/`、`dotnet/route_tracer/` trace 文件引用 | 双证据约束的载体 |

## 输出

按 `skills/shared/IO_PATH_CONVENTION.md`（:252）落盘 `cross/cross_taint_links_{timestamp}.md`，字段：

| 字段 | 说明 |
| ---- | ---- |
| `cross_trace_id` | `XTRACE-{n}`，跨端链唯一 ID |
| 方向 | `forward` / `reverse` |
| node 侧证据 | `EVID_NODE_*` 或 node trace 文件引用（路径:行号） |
| contract 记录引用 | contract_map 行号/记录（`api_contract_map_{ts}.md` 的 matched 记录） |
| dotnet 侧证据 | dotnet route-tracer 文件引用或 `EVID_*`（路径:行号） |
| 闭合状态 | `closed` / `pending` |
| 缺失证据清单 | `missing_node_trace` / `missing_dotnet_trace` / `contract_record_unmatched` 逐条列出 |

产物结构（强制）：对账范围与批次声明、`closed` 区段（已确认链总表 + 逐链详情）、`open` 区段（待验证链 + 缺失证据清单）、误报区段（三态留痕）、`trace_closure_status` 与下一步动作。

与 fullstack-audit-pipeline 阶段 6 的关系：本 Skill 由 fullstack 阶段 6（跨端关联）调用；其输出 `cross/cross_taint_links_{timestamp}.md` 的 XTRACE 链被 `cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` 消费，作为跨端利用链聚合的输入。

**XTRACE 链正式产物（P1 交付，替代 NOT_RUN 占位）**：`cross/exploit_chain/cross_stack_exploit_chains_{timestamp}.md` 每条链必须含：
- `chain_id`：`XTRACE-{n}`
- 链路可行性：`确认可行`（链上所有 C/H 级单点均完成动态复核）/ `推断可行`（含仅静态证据单点）/ `理论可行`（存在假设环节未闭合）
- 影响面评估：影响范围（前端会话/后端数据/租户边界）、攻击复杂度、前置条件清单
- 证据锚点：每环节附 `file:line` 或上游产物路径（前端 Source trace、后端 route trace、contract_map 行）
- 结论不得强于链上最弱证据强度（与 POC 动态验证强制联动）
