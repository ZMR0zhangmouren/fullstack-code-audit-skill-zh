---
name: node-fastify-audit
description: Node.js Fastify 框架专项审计工具。针对 Fastify JSON schema 校验、hook 链、封装上下文与错误处理的框架边界、运行时配置与控制面进行白盒审计。
---

# Fastify 框架专项审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 Fastify 相关的 route schema 校验、hook 链、封装（register）隔离、静态目录、插件配置抓手
- 若项目存在插件封装、装饰器（decorate）、公共 schema 复用等 Fastify 二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（本专项核心输入：确认 hook 链顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于对齐匿名入口、P0/P1 分桶与 preHandler 鉴权覆盖范围）
- 可选：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`（用于将 schema 弱校验/hook 风险与具体入口、副作用链交叉引用）
- 可选：`node/vuln_audit/*_{timestamp}.md`（用于与 nosql/xss/session-cookie 等漏洞专项互相印证）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于对齐 BFF 转发或前后端同构参数来源）

## 重点检查

- route 级 JSON schema 缺失：`schema.body/params/query` 未定义 → 参数弱校验直通 handler（fail-open）
- ajv 配置：`coerceTypes` 开启导致类型强转绕过校验、`removeAdditional` 未开启导致多余字段进入 handler
- hook 链顺序缺陷：`onRequest`/`preHandler` 中未 `reply.send` 短路或注册于封装子上下文、鉴权 hook 被同层后续 hook 覆盖
- 封装上下文（`fastify.register`）隔离缺陷：根实例注册的鉴权 hook 在子封装中失效或未生效
- `@fastify/static` 根目录可控、`index`/`list` 选项开启或置于鉴权之前 → 目录暴露
- 内容类型解析：非 JSON Content-Type 回退到默认解析器（弱校验绕过 schema.body）
- `@fastify/cors` 通配 + `credentials` 组合、`@fastify/rate-limit` 缺失
- `setErrorHandler` 缺失 → 默认错误响应（非生产环境输出堆栈与内部路径）

## 枚举规则（强制细化）

### 1. 框架边界层

- 枚举入口定义方式：`fastify.get/post/route({ method, url, handler })`、`fastify.register(plugin, options)` 插件挂载、`fastify.all` 兜底
- 枚举 hook 链注册：`onRequest` → `preParsing` → `preValidation` → `preHandler` → handler → `onSend` → `onResponse`，标注每层短路条件（`reply.send` 直接返回、`return reply.code(...).send(...)`）
- 枚举封装上下文：`fastify.register` 的插件隔离边界、根实例/子封装实例的 hook 与装饰器作用域
- 枚举静态目录：`@fastify/static` 的 `root` 来源（硬编码/环境变量/用户输入）、`index`、`list`、`prefix` 选项、相对鉴权 hook 的位置
- 识别请求生命周期边界：request → hook 链 → handler → onSend → response，标注 `reply.send` 输出点（供 XSS 专项）

### 2. 运行时配置层

- 枚举 `process.env`、`dotenv`、`.env` 读取点与敏感项（secret、token、DB 连接串）
- 枚举 JSON schema 校验配置：各 route 的 `schema.body/params/query/response` 定义、`ajv.customOptions`（`coerceTypes`/`removeAdditional`）、`attachValidation` 弱化模式
- 枚举内容类型解析：`addContentTypeParser` 自定义解析器、非 JSON 类型回退路径、`contentTypeParser` 覆盖
- 枚举插件配置：`@fastify/cookie`（signed/secure）、`@fastify/cors`、`@fastify/rate-limit`、`@fastify/session`、`fastify-helmet`
- 枚举安全头与跨域配置：`@fastify/helmet`、`@fastify/cors({ origin, credentials })`
- 若存在插件封装、公共 schema 复用等二次封装，必须逐层展开到真实 route/hook 调用点

### 3. 前置控制面层

- 枚举鉴权覆盖范围：`preHandler` 中的 `jwt.verify`/自定义鉴权、`@fastify/auth`、`onRequest` 全局鉴权 hook 是根实例还是仅子封装注册
- 识别路由级鉴权缺失：比对路由清单与鉴权 hook 覆盖，标记未覆盖路由与 `fastify.all` 兜底路由
- 枚举速率限制：`@fastify/rate-limit` 配置、与 `request.ip` 来源的联动（反代伪造 IP 绕过限流）
- 枚举请求大小限制：`bodyLimit` 全局配置、route 级 `bodyLimit`、上传限制（`@fastify/multipart` 的 limits）

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| schema 校验 | route 定义 `schema: { body: {...} }` | 检查各 route 是否定义 schema.body/params/query 及 ajv 选项是否弱化 | schema 明确且 `coerceTypes` 未开 → ✅ 安全；schema 缺失或 `attachValidation` 弱化 → 🔴 弱校验（fail-open） |
| hook 顺序 | `onRequest`/`preHandler` 中鉴权后 `done()`/`reply.send` 短路 | 按 hook 链顺序检查鉴权 hook 相对 handler 的位置与短路条件 | 鉴权 hook 先于 handler 且无条件放行 → ✅ 安全；鉴权挂于 handler 后/未注册 → 🔴 高危 |
| 封装隔离 | 根实例注册全局鉴权 `onRequest` hook | 检查鉴权 hook 的注册上下文（根/子封装）是否覆盖全部 route | 根实例全局覆盖或子封装内 fail-close → ✅ 安全；子封装覆盖不完整 → ⚠️ 待确认 |
| 错误处理 | `fastify.setErrorHandler((err, req, reply) => ...)` | 检查是否设置自定义错误处理器及响应内容是否含堆栈/内部路径 | 自定义处理器且响应净化 → ✅ 安全；缺失 → 🔴 默认堆栈泄露（fail-open） |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认风险候选`：框架配置或控制面缺失可能导致外部输入绕过、权限扩大或敏感信息暴露
- `待确认`：上下文显示可疑模式，但入口覆盖范围、barrier 行为或调用链不清晰
- `误报`：配置已显式启用 fail-close，或风险点已被其他控制面覆盖

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到框架控制面与具体入口/sink 发生关联的证据 → `确认风险`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知/非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- route 未定义 `schema.body/params/query` 且入口可达，外部输入直通 handler（`EVID_NODE_CFG_SECURITY_SWITCH`）
- `coerceTypes` 开启或 `attachValidation` 弱化，类型强转/校验失败静默透传（`EVID_NODE_CFG_RUNTIME_SETTING`）
- `setErrorHandler` 缺失，默认错误响应输出堆栈与内部路径（`EVID_NODE_CFG_ERR_HANDLER`）
- 鉴权 hook 注册于子封装而存在未覆盖 route，或 `onRequest` 中未短路放行非白名单请求（`EVID_NODE_CFG_MIDDLEWARE_ORDER`）
- `@fastify/cors` 通配 + `credentials` 组合，且存在携带 Cookie 的受保护接口

### ⚠️待验证

- 封装上下文隔离不清：鉴权 hook 在根实例注册但存在 `fastify.register` 子实例覆盖行为，静态无法确认全部 route 生效范围
- `coerceTypes` 等 ajv 选项经插件封装注入，无法静态确认实际编译生效配置
- 非 JSON Content-Type 回退路径依赖客户端实际发送头，静态无法枚举全部回退场景
- 错误响应是否泄露堆栈取决于 `NODE_ENV` 运行时值，静态无法确认

### 误报

- 各 route 均显式定义 `schema` 且 ajv 配置 fail-close（未知字段被拒/剥离）
- 鉴权 hook 在根实例 `onRequest` 全局注册且无条件拦截
- `setErrorHandler` 已注册且响应已净化（无堆栈/内部路径）
- CORS 未通配或未携带 `credentials`，`@fastify/static` root 固定且置于鉴权之后

## 测试建议（强制）

### 正向测试

- 无鉴权直接请求受保护 route → 应被拒绝（401/403），验证 hook 链覆盖
- 构造违反 schema 的 body（错误类型/多余字段）请求 → 应返回 400 而非进入 handler
- 触发异常请求 → 响应应为净化错误页，不包含堆栈/内部路径
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 合法请求完整通过 hook 链（鉴权 + 限流 + schema 校验）正常返回
- 符合 schema 的边界值请求可用，未被误拒
- 生产模式（`NODE_ENV=production`）下错误响应不泄露堆栈

### 回归测试

- hook 链顺序或封装结构变更后重验鉴权覆盖与 schema 校验
- 新增 route 必须纳入 schema/鉴权覆盖清单后复测
- 错误处理器/内容类型解析器改动后复测堆栈泄露与 400/413 行为

## 证据引用

- `EVID_NODE_CFG_SECURITY_SWITCH`
- `EVID_NODE_CFG_RUNTIME_SETTING`
- `EVID_NODE_CFG_ERR_HANDLER`
- `EVID_NODE_CFG_MIDDLEWARE_ORDER`
- `EVID_NODE_NOSQL_TYPE_COERCE_GUARD`（schema 校验弱化场景联调 node-nosql-audit）
- `EVID_NODE_SESS_COOKIE_FLAGS`（@fastify/cookie/session 配置面联调 node-session-cookie-audit）

## 输出

- `node/framework_audit/fastify_{timestamp}.md`
- 必须写明：route 入口与 schema 校验覆盖（含缺失清单）、hook 链顺序与短路条件、封装上下文隔离、静态目录暴露面、运行时配置（ajv/bodyLimit/CORS/rate-limit）、鉴权覆盖范围与未覆盖 route
- 必须写明环境差异：`NODE_ENV` 分支、`request.ip` 反代依赖、生产/开发配置差异
- 消费关系：影响漏洞强结论时必须显式写明如何被 `node/route_tracer`、各 `node-vuln-audit` 专项（nosql/xss/session-cookie 等）与 `node-audit-pipeline` 消费
