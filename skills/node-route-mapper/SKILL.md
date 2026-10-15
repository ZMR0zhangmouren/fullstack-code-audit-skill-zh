---
name: node-route-mapper
description: Node.js Web 入口与参数映射分析工具。从 http.createServer、Express 等源码中提取完整入口、参数结构与请求模板，并生成下游消费的路由与中间件清单。
---

# Node.js Route & Endpoint Mapper

## 共享抓手索引引用

本 Skill 的枚举关键字、优先对象与记录口径以 `skills/shared/NODE_AUDIT_GRABBER_INDEX.md` 为单一真源，按 入口定义 / 绑定与参数 / 前置控制 三层检索。路径与产物命名遵循 `skills/shared/IO_PATH_CONVENTION.md` 中 `node/` 子树约定。

## 输入依赖

用户提供：

- `node_source_path`：Node.js 项目、仓库根目录或包含 `package.json` 的目录（必需）。
- `node/stack_detect/stack_detect_{timestamp}.md`：阶段 0 技术栈检出结果，用于选择适配器（可选，推荐）。
- `context_path`：反向代理、网关前缀、Next.js basePath 等外部路径前缀（可选，必须有配置或代码证据来源）。

## 适配器策略

P1 内置适配器仅覆盖 通用 Node（`http.createServer`）与 Express。检测到 NestJS / Next.js / Koa / Fastify / Nuxt 时，按 `NODE_AUDIT_GRABBER_INDEX.md` 对应关键字枚举；无法闭合的模块记入 `route_module_inventory` 的未映射清单，不得虚构路由。

- 通用 Node：解析 `createServer` 回调内的 `req.url`、`req.method` 与手动路由分发。
- Express：解析 `express()`、`app` / `router.get|post|put|delete|patch|all|use`、挂载前缀链、中间件顺序。
- NestJS / Next.js / Koa / Fastify / Nuxt：使用对应装饰器、文件约定、插件注册关键字；当前阶段若不能精确还原最终路径与 handler，记录 `adapter_unresolved` 原因。
- 默认排除 `node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`、`coverage/` 目录；`package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` 仅用于供应链审计，不纳入路由枚举面。

## 枚举规则（强制细化）

逐条收录 `NODE_AUDIT_GRABBER_INDEX.md` 的入口定义与绑定参数抓手：

### 入口定义抓手

| 类型 | 优先关键字 | 重点记录 |
| ---- | ---- | ---- |
| 通用 Node | http.createServer, createServer, req.url, req.method | 原生路由分发、方法判断 |
| Express | express(), Router(), app.get, app.post, app.put, app.delete, app.patch, app.all, app.use, router.use | 路由模板、HTTP 方法、挂载前缀、中间件链 |
| NestJS | @Controller, @Get, @Post, @Put, @Delete, @Patch, @All, @UseGuards, @UseInterceptors | 装饰器路由、Guard/Interceptor 覆盖 |
| Next.js | app/api/**/route.{js,ts}, pages/api/**, export function GET, export function POST, NextRequest, middleware.ts | 文件约定路由、HTTP 方法导出、边缘中间件 |
| Koa | new Koa(), koa-router, router.get, router.post, app.use | 路由、ctx 传递 |
| Fastify | fastify.route, fastify.get, fastify.post, fastify.register, addHook | 路由注册、插件作用域、钩子 |
| Nuxt/Nitro | defineEventHandler, getQuery, readBody, server/api/** | 服务端入口、参数读取 |

### 绑定与参数抓手

| 类型 | 优先关键字 | 重点记录 |
| ---- | ---- | ---- |
| Express 系 | req.params, req.query, req.body, req.headers, req.cookies | 参数来源、名称映射 |
| Koa 系 | ctx.params, ctx.query, ctx.request.body, ctx.headers, ctx.cookies | 同上 |
| NestJS | @Body(), @Query(), @Param(), @Headers(), ValidationPipe | DTO 展开字段、校验管道白名单 |
| Next/Nuxt | await request.json(), request.nextUrl.searchParams, getQuery(), readBody(), getRouterParam() | 参数来源 |
| 文件输入 | multer, busboy, formidable, multipart | 文件名、dest、limits |

每条路由必须记录：

- `route_id`：`R{序号}`，全局唯一，与 `params_{timestamp}.md` 逐条对应。
- `route_method`：HTTP 方法或操作名。
- `route_path_template`：最终路径模板（含挂载前缀链）。
- `source_file:line`：声明位置。
- `mount_prefix_chain`：从应用根到 handler 的 `app.use` / `router.use` 前缀链。
- `param_source`：`req.params` / `req.query` / `req.body` / `req.headers` / `req.cookies` 或框架等价物。
- `handler_identifier`：函数名、控制器方法或处理器标识。
- `adapter_type`：`generic-node` / `express` / `nestjs` / `nextjs` / `koa` / `fastify` / `nuxt`。

### 中间件即鉴权面

`middleware_inventory` 逐条记录：

- `middleware_name`：中间件函数名或引入模块名。
- `mount_path_prefix`：挂载路径前缀；全局中间件写 `/`。
- `is_auth`：是否属于鉴权类（`passport.authenticate`、`express-jwt`、`expressjwt`、`jwt.verify`、`express-session`、`cookie-session`、`next-auth`、`getServerSession`、`@UseGuards` 等）。
- `is_global`：是否全局挂载。

## frontend_outbound 出站端点采集（强制，2026-09-20）

采集前端（或 node BFF）发起的外部 API 调用端点全集，供跨端契约对账（cross-stack-contract-mapper）与功能映射（node-feature-api-mapper）消费。方法成熟样例见 2026-09-17 run 产物 `frontend_outbound_2026_09_17_15_18.md`（方法三件套）：

1. **rg 端点枚举**：`rg -o "baseUrl \+ '[^']+'" {src 范围}`（排除 `node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`、`coverage/`），结果按路径去重，得 baseUrl 相对路径全集；`baseUrl` 变量名按项目实际替换（如 `apiUrl`、`API_BASE`）。
2. **生成客户端方法表**：生成式 API 客户端（NSwag / Swagger codegen / openapi-typescript 产物）逐方法记录**方法名 → HTTP 方法 → 端点路径**，以生成签名与文件行号为准（不凭方法名臆测方法）。
3. **客户端构造复核**：定位客户端构造入口（如 `src/api/index.ts`），记录 baseUrl 来源（config 下发 / 硬编码 / 环境变量）、鉴权注入方式（fetch 包装 / Bearer 头 / 拦截器）、以及非生成客户端的出站通道（SSO 浏览器跳转、`window.open`、本 BFF 转发等），逐通道列入「出站通道」表。

产物：`node/route_mapping/frontend_outbound_{timestamp}.md`（输出表已登记）；结构：头部方法声明（rg 模式 + 客户端构造复核位置）→ 出站通道表（通道 / 目标 / 位置 / 说明）→ 端点清单按 baseUrl 分组（方法以生成客户端方法表为准，端点清单必须逐方法标注 (method, path)，方法不确定者逐条列入下一节，禁止双方法保守上界占位）→ 「## 方法不确定清单」节（含组件 / 调用点 / 原因三列）→ 统计（出站端点总数 / 出站目标数）。

每条端点的方法集合执行下方「frontend_outbound 出站端点方法级配对（强制，2026-09-20）」节：逐方法配对，方法不确定条目的落点见该节（写入产物自备「## 方法不确定清单」节，禁止双方法保守上界）。

## 覆盖门禁（强制）

镜像 `dotnet-route-mapper` 的 Controller Inventory 与 API Coverage Gate 语义。

1. 在生成 `node/route_mapping/routes_{timestamp}.md` 之前，必须先生成 `node/route_mapping/route_module_inventory_{timestamp}.md`。
2. `route_module_inventory` 至少包含：

| 字段 | 说明 |
| ---- | ---- |
| module_name | 路由模块 / 控制器 / 文件约定目录名 |
| module_file | 文件路径 |
| route_prefix | 挂载前缀 |
| route_count | 该模块声明路由总数 |
| mapped_routes | 已映射路由数 |
| in_route_mapping | 是否已纳入 routes |
| unmapped_reason | 未映射原因 |

3. 只要存在未映射活动路由模块，`api_coverage_status` 必须为 `PARTIAL`。
4. 必须生成 `node/quality/api_coverage_gate_{timestamp}.md`，至少包含：
   - `active_route_module_total`
   - `mapped_route_module_count`
   - `mapped_route_count`
   - `unmapped_route_modules`
   - `unmapped_routes`
   - `api_coverage_percent`
   - `api_coverage_status`
   - `unique_path_count`
   - `method_path_count`
   - `pipeline_execution_allowed_completed`
   - `reason`
5. 当 `api_coverage_status=PARTIAL` 时：
   - 必须落盘 `node/quality/unmapped_routes_{timestamp}.md`，包含未映射模块、未映射路由、原因、下一轮补图批次建议。
   - 必须进入循环补图，每轮刷新 `route_module_inventory`、`api_coverage_gate`、`unmapped_routes`。
   - 仅当未映射活动模块与路由均为 0，或用户显式接受 `PARTIAL` 时，方可停止。
6. 当 `api_coverage_percent < 100%` 时，禁止将 `pipeline_execution` 标记为 `COMPLETED`，禁止输出“全量审计完成”措辞。

### frontend_outbound 出站端点方法级配对（强制，2026-09-20）

- 采集规则本体（rg 端点枚举 / 生成客户端方法表 / 客户端构造复核三件套）见本节上方「frontend_outbound 出站端点采集」节，本节制配对与计数口径
- `node/route_mapping/frontend_outbound_{timestamp}.md` 每条出站端点的方法集合必须**方法级配对**：逐 HTTP 方法逐一与后端路由对账，每个已确定方法单独计一条 (method, path) 配对记录
- **禁止双方法保守上界标注**：方法无法从源码确定时，禁止把条目写成「GET/POST」之类的双方法保守上界充数
- 方法不确定条目写入 `frontend_outbound_{timestamp}.md` 产物自备「## 方法不确定清单」节（含组件 / 调用点 / 原因三列），禁止写入 `unmapped_routes`——`unmapped_routes` 为入站未映射语义，写入会污染 api_coverage_gate 的入站门禁统计；方法不确定条目不得计入 matched
- 计数口径与 `IO_PATH_CONVENTION.md` 路由计数双字段口径一致：`method_path_count` 只统计方法已确定的 (method, path) 组合

## 输出

按 `skills/shared/IO_PATH_CONVENTION.md` 中 Node.js 与跨端产物路径落盘：

| 产物 | 物理路径 |
| ---- | ---- |
| route_module_inventory | `node/route_mapping/route_module_inventory_{timestamp}.md` |
| routes | `node/route_mapping/routes_{timestamp}.md` |
| frontend_outbound | `node/route_mapping/frontend_outbound_{timestamp}.md` |
| params | `node/route_mapping/params_{timestamp}.md` |
| middleware_inventory | `node/route_mapping/middleware_inventory_{timestamp}.md` |
| 阶段索引 | `node/route_mapping/index_{timestamp}.md` |
| API 覆盖门禁 | `node/quality/api_coverage_gate_{timestamp}.md` |
| 未映射清单（PARTIAL 时强制） | `node/quality/unmapped_routes_{timestamp}.md` |
| 补图循环记录（建议） | `node/quality/route_mapping_backfill_loop_{timestamp}.md` |

`route_id` 规则 `R{序号}` 全局唯一，被下游 Task 8 / 9 / 11–18 消费。`routes` 与 `params` 条目必须一一对应，`route_id` 不得漂移。

### routes 条目最小字段

routes 文件头部必须含 `unique_path_count` / `method_path_count` 双字段，口径见 `IO_PATH_CONVENTION.md` 路由计数双字段口径节。

- `route_id`
- 入口类型：`HTTP` / `HUB` / `GRAPHQL` / `SERVERLESS` / `CLI`
- HTTP 方法或操作名
- 路由路径规则
- 路由声明方式：`attribute` / `convention` / `file-based` / `manual`
- 处理器标识
- 位置：`file:line`
- 挂载前缀链
- 参数概览
- 返回模板类型

### params 条目最小字段

- `route_id`
- Path / Query / Body / Header / Cookie / File 参数表
- 完整请求模板或调用模板

### 输出前自检

- [ ] `routes` 与 `params` 的 `route_id` 一致且逐条对应。
- [ ] 无省略占位符。
- [ ] 挂载前缀链已展开。
- [ ] 中间件清单已区分鉴权类与全局性。
- [ ] `api_coverage_status` 与 `unmapped_routes` / `pipeline_execution` 状态联动正确。
- [ ] `frontend_outbound` 出站端点已方法级配对，无双方法保守上界标注；方法不确定条目已写入产物自备「## 方法不确定清单」节，未写入 `unmapped_routes`。
