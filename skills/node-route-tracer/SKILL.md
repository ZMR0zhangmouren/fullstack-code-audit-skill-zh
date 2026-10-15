---
name: node-route-tracer
description: Node.js 入口到 Sink 的数据流追踪工具。消费 node-route-mapper 的路由与参数，依据 NODE_SINK_REFERENCE 判定 Sink，输出 trace 证据与 trace_status，不输出漏洞结论。
---

# Node.js Route Tracer

## 共享抓手索引引用

本 Skill 的 Source 关键字、参数来源与 Sink 判定统一引用以下共享索引：

- `skills/shared/NODE_AUDIT_GRABBER_INDEX.md`：Source 与参数抓手真源。
- `skills/shared/NODE_SINK_REFERENCE.md`：Sink API、可控参数位与参考 Barrier 的唯一基准。
- `skills/shared/EVIDENCE_POINT_IDS.md`：EVID_NODE_* 证据点 ID 真源。
- `skills/shared/IO_PATH_CONVENTION.md`：产物路径与命名约定。

## 输入依赖

- `node_source_path`：Node.js 项目根目录（含 `package.json`）。
- `node/route_mapping/routes_{timestamp}.md`：上游路由清单，含 `route_id`。
- `node/route_mapping/params_{timestamp}.md`：与 `routes` 逐条对应的参数结构。
- `node/route_mapping/middleware_inventory_{timestamp}.md`：中间件清单，用于追踪前置控制面。
- `node/cross_analysis/trace_batch_plan_{timestamp}.md`：分批追踪计划（批次大小、route_id 集合、执行顺序）。
- `node/stack_detect/stack_detect_{timestamp}.md`（可选）：技术栈检出结果，用于选择适配器与 Sink 包名。
- `node/route_mapping/index_{timestamp}.md`（可选）：阶段索引，用于确认上游产物版本一致。

## Source 定义

Source 为外部可控输入首次进入处理链的位置。本 Skill 覆盖 `NODE_AUDIT_GRABBER_INDEX.md`「绑定与参数抓手」全表，并额外覆盖 `process.env` 中由运行时注入、非配置面硬编码的取值点。

| 类型 | 优先关键字 / 取值点 | 重点记录 |
| ---- | ---- | ---- |
| Express 系 | `req.params`, `req.query`, `req.body`, `req.headers`, `req.cookies` | 参数名、绑定源、是否经 body-parser / cookie-parser 转换 |
| Koa 系 | `ctx.params`, `ctx.query`, `ctx.request.body`, `ctx.headers`, `ctx.cookies` | 同上 |
| NestJS | `@Body()`, `@Query()`, `@Param()`, `@Headers()` 展开字段 | DTO 字段映射、ValidationPipe 白名单 |
| Next/Nuxt | `await request.json()`, `request.nextUrl.searchParams`, `getQuery()`, `readBody()`, `getRouterParam()` | 异步读取点与字段名 |
| 文件输入 | `multer` 的 `req.file` / `req.files`，`busboy` 的 `info.filename`，`formidable` 的 `file.originalFilename` | 原始文件名、Content-Type、落点配置 |
| 环境变量 | `process.env.{NAME}`（运行时注入面） | 取值点、是否进入分支条件 / 目标 URL / 命令 / 模板路径 |

`process.env` 排除项：仅作为静态配置阈值、开关默认值、日志级别等配置面的读取不视为 Source；一旦 `process.env` 取值进入响应构造、命令拼接、URL 组装、模板路径选择、权限判断，则按 Source 追踪。

## Propagator 规则

Propagator 指 Source 到达 Sink 之间的数据传递、拆分、合并或变形形式。追踪时必须识别以下模式并记录变量名变化：

| 传播形式 | 典型代码模式 | 追踪要求 |
| ---- | ---- | ---- |
| 解构赋值 | `const { id, name } = req.body` | 记录原始 Source 字段与局部变量名的映射 |
| JSON.parse | `const obj = JSON.parse(req.body)` | 记录解析后的字段路径与 Source 的对应关系 |
| await 链 | `const data = await service.foo(param)` | 记录 await 前后的变量传递、中间返回对象字段 |
| 中间件向 req 挂载 | `req.user = decoded`, `req.tenant = header`, `req.locals.x = y` | 记录挂载点、挂载值来源、下游读取位置 |
| lodash merge / assign / clone | `_.merge(target, source)`, `_.assign(a, b)`, `_.cloneDeep(obj)` | 记录合并前后对象字段、Source 是否进入目标对象 |
| 字符串模板拼接 | `` `SELECT * FROM t WHERE id = ${id}` ``, `url + path` | 记录拼接位置、参与拼接的 Source 字段、最终字符串使用点 |

追踪时应按数据流顺序给出：Source 点 → 首次赋值/解构 → 中间转换（parse/await/merge） → 进入 Sink 前的最终变量形态。

## Sink 判定

Sink 判定以 `skills/shared/NODE_SINK_REFERENCE.md` 为唯一基准，禁止自行扩展 Sink 定义。

判定动作：

1. 按 `NODE_SINK_REFERENCE.md` 的 Sink API 清单在源码中定位调用点。
2. 核对调用点参数是否来自 Source 或经 Propagator 传递的变量。
3. 命中后记录对应 `EVID_NODE_*` 证据点 ID（以 `skills/shared/EVIDENCE_POINT_IDS.md` 的 NODE 命名空间为准，逐字引用）。

| Sink 类型 | 典型 API | 对应 EVID_NODE_* ID（命中即记录） |
| ---- | ---- | ---- |
| PROTO | `_.merge`, `_.assign`, `_.defaultsDeep`, `Object.assign` 接不可信对象 | `EVID_NODE_PROTO_MERGE_SINK`, `EVID_NODE_PROTO_MAGIC_KEY_CONTROL`, `EVID_NODE_PROTO_KEY_FILTER_ABSENT_OR_BYPASS`, `EVID_NODE_PROTO_GADGET_TRIGGER` |
| CMD | `child_process.exec`, `execSync`, `spawn({shell:true})`, `execFile` | `EVID_NODE_CMD_EXEC_POINT`, `EVID_NODE_CMD_STRING_CONSTRUCTION`, `EVID_NODE_CMD_USER_PARAM_TO_CMD`, `EVID_NODE_CMD_ARG_ARRAY_OR_ALLOWLIST` |
| SSRF | `axios.get`, `fetch`, `got`, `request`, `undici.request`, `http.get` | `EVID_NODE_SSRF_HTTP_CALL_POINT`, `EVID_NODE_SSRF_URL_CONSTRUCTION`, `EVID_NODE_SSRF_ALLOWLIST`, `EVID_NODE_SSRF_REDIRECT_FOLLOW` |
| NOSQL | `Model.find(query)`, `collection.findOne`, `$where`, `$regex` | `EVID_NODE_NOSQL_QUERY_POINT`, `EVID_NODE_NOSQL_RAW_OBJECT_PASS`, `EVID_NODE_NOSQL_OPERATOR_INJECTION`, `EVID_NODE_NOSQL_TYPE_COERCE_GUARD` |
| UPLOAD | `multer`, `busboy`, `formidable` | `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`, `EVID_NODE_UPLOAD_FILENAME_SANITIZE`, `EVID_NODE_UPLOAD_FILTER_LIMITS`, `EVID_NODE_UPLOAD_ACCESSIBILITY` |
| XSS | 服务端：`res.send(markup)`、`res.render(view, locals)`；SSR / 同构渲染上下文中的客户端：`dangerouslySetInnerHTML`、`v-html` | `EVID_NODE_XSS_OUTPUT_POINT`, `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT`, `EVID_NODE_XSS_ENCODE_OR_SANITIZE`, `EVID_NODE_XSS_SSR_HYDRATION` |
| SSTI | `ejs.render`, `pug.compile`, `nunjucks.renderString`, `handlebars.compile` | `EVID_NODE_SSTI_RENDER_POINT`, `EVID_NODE_SSTI_TEMPLATE_CONCAT`, `EVID_NODE_SSTI_TEMPLATE_NAME_CONTROL` |
| SESS | `jwt.sign`, `jwt.verify`, `res.cookie` | `EVID_NODE_SESS_JWT_SIGN_VERIFY_CONFIG`, `EVID_NODE_SESS_JWT_ALG_PINNED`, `EVID_NODE_SESS_SECRET_SOURCE`, `EVID_NODE_SESS_COOKIE_FLAGS`, `EVID_NODE_SESS_LIFECYCLE` |

命中 Sink 后，必须在 trace 中给出：Sink 类型、具体 API、调用点 `file:line`、参数来源映射、是否经过编码 / 白名单 / 授权 / 配置保护、证据完整度/可信度（仅指证据链的完整与可信程度，不等价于漏洞风险等级）。

上表仅为当前 `EVIDENCE_POINT_IDS.md` NODE 命名空间已登记 ID 的类型示例；命中未列出的类型（SQL / FILE / WRITE / ARCHIVE / REDIR / DESER / EXPR / REDOS / CRYPTO / CSRF / CFG / DOMXSS 等）时，一律按 `NODE_SINK_REFERENCE.md` 的 Sink API 清单记录调用点与可控参数位，并暂记 `EVID_NODE_*` 待补录标记，待对应 P2 专项证据 ID 登记后回填，禁止因表内无行而跳过记录。

## 分批追踪（强制）

本 Skill 按 `node/cross_analysis/trace_batch_plan_{timestamp}.md` 执行分批追踪，不一次性全量处理。分批大小必须符合 `shared/IO_PATH_CONVENTION.md` 中 `trace_batch_max_size` 的 coverage_mode 阈值（FULL 10–30；SAMPLE 5–10 且不得超过 10），由 `node-audit-pipeline` 阶段 3 在计划中落实，本 Skill 只按计划执行。

每批次执行：

1. 读取当前批次 `route_id` 集合。
2. 从 `routes_{timestamp}.md` 与 `params_{timestamp}.md` 还原入口与请求模板。
3. 按「Source → Propagator → Sink」逐层追踪，记录调用链层级与分支路径。
4. 为每个 `route_id` 写入 `node/route_tracer/{route_id}/trace_{timestamp}.md`。
5. 更新 `trace_status`。

`trace_status` 五态：

| 状态 | 含义 |
| ---- | ---- |
| NOT_STARTED | 已列入批次计划但尚未开始追踪 |
| IN_PROGRESS | 追踪进行中，已有部分链路证据 |
| DONE_OPEN | 追踪完成，存在可到达 Sink 的开放链路（参数可控性已证明） |
| DONE_CLOSED | 追踪完成，Sink 不存在或参数不可控（链路闭合为无风险） |
| BLOCKED | 追踪被阻断（缺少关键上游产物、源码不可访问、依赖无法解析） |

`trace_status` 必须回写到 `node/quality/manifest_{run_id}.md` 的对应 `route_id` 行，供 pipeline 与 trace-gate 消费。

## 未闭合风险池（强制）

未闭合 trace 必须保留并写明缺失证据，禁止静默删除。

未闭合场景包括：

- Source 进入 handler 后无法定位后续使用点。
- Propagator 链中存在异步分支、队列投递、事件发布，当前上下文无法继续。
- Sink 调用点存在，但参数来源映射缺失或无法证明可控。
- 分支条件存在但执行路径不可证明。
- 依赖运行时实现（如 DI 实现、中间件顺序）无法静态确认。

处理要求：

1. 在 `node/route_tracer/{route_id}/trace_{timestamp}.md` 的「Trace 完整性声明」中按 `trace_status` 五态标记：存在可到达 Sink 但链路未完全闭合 → `DONE_OPEN`；无法证明可控或 Sink 不存在 → `DONE_CLOSED`；上游产物缺失 → `BLOCKED`，并在缺失项中说明「局部链路」。
2. 逐条列出缺失证据：调用链层级 / 分支 / 映射 / 配置 / 环境依赖。
3. 将未闭合 trace 的 `route_id`、`缺失证据摘要`、`建议补证动作` 汇总到 `node/route_tracer/unclosed_trace_pool_{timestamp}.md`。
4. `unclosed_trace_pool_{timestamp}.md` 必须随每批次更新，不得清空未解决项。
5. 未闭合 trace 不得用于支撑「确认可利用」或高强度漏洞结论；仅可作为待验证风险池供后续专项或动态复核参考。

## 输出

按 `skills/shared/IO_PATH_CONVENTION.md` 中 `node/route_tracer/{route_id}/...` 约定落盘。

| 产物 | 物理路径 |
| ---- | ---- |
| 单路由追踪 | `node/route_tracer/{route_id}/trace_{timestamp}.md` |
| 单路由追踪汇总 | `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` |
| 未闭合风险池 | `node/route_tracer/unclosed_trace_pool_{timestamp}.md` |
| 阶段索引 | `node/route_tracer/index_{timestamp}.md` |
| 空结果说明（如无 trace 产出） | `node/route_tracer/empty_result_{timestamp}.md` |

`trace_{timestamp}.md` 最小章节：

1. 追踪入口（来自 route-mapper 的 method / path / handler）
2. 完整请求模板
3. 参数进入点（Source 表）
4. 调用链层级证据（逐层，含中间件、handler、service、util）
5. 分支路径追踪
6. 参数可控性矩阵
7. Sink 定位（参数映射）
8. Sink Summary
9. Trace 完整性声明（含 `trace_status` 与缺失项列表）
10. Sink Evidence Type Checklist（按命中的 Sink 类型列出 EVID_NODE_* 证据点）

`trace_summary_{timestamp}.md` 至少包含：

- `route_id`
- `trace_status`
- 命中 Sink 类型集合
- 命中 EVID_NODE_* ID 集合
- 参数可控性最高等级
- 缺失证据摘要
- 下一步动作

输出前自检：

- [ ] `trace_status` 已按五态之一写入。
- [ ] 命中 Sink 已记录对应 `EVID_NODE_*` ID。
- [ ] 未闭合 trace 已写入 `unclosed_trace_pool_{timestamp}.md`。
- [ ] 产物路径与命名符合 `IO_PATH_CONVENTION.md` 的 `node/` 子树约定。
- [ ] 未输出任何漏洞结论、风险等级或修复建议。
