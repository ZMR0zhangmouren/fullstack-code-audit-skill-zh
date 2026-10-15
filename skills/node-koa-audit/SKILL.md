---
name: node-koa-audit
description: Node.js Koa 框架专项审计工具。针对 Koa 洋葱模型中间件链、ctx 传递、body 解析与错误处理的框架边界、运行时配置与控制面进行白盒审计。
---

# Koa 框架专项审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 Koa 相关的中间件链（洋葱模型）、ctx 数据传递、body 解析、静态目录、会话与安全头配置抓手
- 若项目存在 app.use 组合器、中间件工厂、ctx 增强扩展等 Koa 二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（本专项核心输入：确认洋葱链注册顺序与 `await next()` 短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于对齐匿名入口、P0/P1 分桶与鉴权中间件覆盖范围）
- 可选：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`（用于将 ctx 数据流/中间件风险与具体入口、副作用链交叉引用）
- 可选：`node/vuln_audit/*_{timestamp}.md`（用于与 xss/session-cookie/file-upload 等漏洞专项互相印证）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于对齐 BFF 转发或前后端同构参数来源）

## 重点检查

- 洋葱模型短路缺陷：鉴权/安全中间件未 `await next()` 或注册在路由之后 → 后续中间件与 handler 直接跳过鉴权
- `ctx.onerror` 默认处理：未自定义错误捕获时，非生产环境默认输出堆栈与内部路径到响应（fail-open）
- `koa-body` / `koa-bodyparser` 未设大小限制（默认 1mb 需确认）或 multipart 配置过宽 → 超大请求体/异常 Content-Type 解析面
- `koa-static` 根目录可控、启用 `index`/`hidden` 选项或置于鉴权之前 → 目录暴露/敏感文件读取
- CORS 通配（`@koa/cors` `origin: '*'`）与 `credentials` 组合 → 任意来源跨域携带 Cookie
- `koa-session` 配置缺陷：默认 `key`、未启用 `signed`、`cookie.secure` 未设、滚动续期（rolling）策略不当
- `ctx.state` 全局共享数据注入点与下游消费面（联调各 vuln 专项）
- `ctx.request.body` 在解析器挂载前被访问 → undefined 静默透传（fail-open）

## 枚举规则（强制细化）

### 1. 框架边界层

- 枚举中间件链注册：`app.use(...)` 按注册顺序记录洋葱层，标注每层是否 `await next()`、有无条件短路（`return ctx.body = ...` 直接返回）
- 枚举路由接入方式：`koa-router`（`router.get/post`、`router.allowedMethods`）、`@koa/router`、自定义路由分发中间件
- 枚举静态目录：`koa-static(root, options)` 的 `root` 来源（硬编码/环境变量/用户输入）、`index`、`hidden`、`defer` 选项、相对鉴权中间件的位置
- 识别请求生命周期边界：request → 洋葱外层 → handler → 洋葱内层 → response，标注 `ctx.body` 直接赋值输出点（供 XSS 专项）
- 识别框架默认行为：404 兜底、`ctx.onerror` 默认错误处理（堆栈泄露面）

### 2. 运行时配置层

- 枚举 `process.env`、`dotenv`、`.env` 读取点与敏感项（secret、token、DB 连接串）
- 枚举 body 解析配置：`koa-bodyparser({ limit, onerror })`、`koa-body`（multipart/limits/formidable 选项）、解析器挂载位置
- 枚举 ctx 数据绑定：`ctx.query`、`ctx.params`、`ctx.request.body`、`ctx.headers`、`ctx.state` 注入点
- 枚举会话配置：`koa-session`（`key`/`signed`/`cookie.secure`/`rolling`/store）、Cookie 选项
- 枚举安全头与跨域配置：helmet/koa-helmet、`@koa/cors`、CSP、HSTS
- 若存在中间件组合器、ctx 增强等二次封装，必须逐层展开到真实 `app.use`/解析器调用点

### 3. 前置控制面层

- 枚举鉴权覆盖范围：`passport`（ctx.state.user）、`koa-jwt`、自定义鉴权中间件是洋葱外层全局挂载还是仅部分路由
- 识别路由级鉴权缺失：比对路由清单与鉴权中间件覆盖，标记未覆盖路由与动态注册路由
- 枚举速率限制：`koa-ratelimit` 等配置、与 `ctx.ip` 来源的联动（反代伪造 IP 绕过限流）
- 枚举请求大小限制：body `limit`、multipart 上传限制（`formidable` 的 `maxFileSize`/`maxFields`）

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 洋葱顺序 | 鉴权中间件 `app.use` 于路由之前并 `await next()` 放行 | 按注册顺序逐层列出中间件，检查鉴权层相对路由层的位置及是否无条件 `await next()` | 鉴权为最外层且放行后无绕过 → ✅ 安全；鉴权挂于路由之后或条件短路 → 🔴 高危 |
| 解析器限制 | `koa-bodyparser({ limit: '1mb' })` | 检查 body 解析器 `limit`/multipart 选项及挂载位置 | 明确 `limit` 且 multipart 限制收紧 → ✅ 安全；未配置 `limit` 或 multipart 无限制 → ⚠️ 待确认 |
| 鉴权覆盖 | 洋葱外层全局鉴权中间件或逐路由 `koa-jwt` | 比对路由清单与鉴权中间件覆盖范围，含动态注册路由 | 全局或逐路由 fail-close → ✅ 安全；存在可达的无鉴权路由 → 🔴 高危 |
| onerror 堆栈泄露 | 自定义 `app.on('error')`/错误中间件捕获并净化响应 | 检查是否覆盖 `ctx.onerror` 默认行为及响应内容是否含堆栈/内部路径 | 错误已捕获且响应净化 → ✅ 安全；依赖 `ctx.onerror` 默认输出 → 🔴 堆栈泄露（fail-open） |

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

- `EVID_NODE_CFG_MIDDLEWARE_ORDER` 显示鉴权中间件注册于路由之后或存在未 `await next()` 的短路层，且受保护入口可达
- 未覆盖 `ctx.onerror` 默认行为，错误响应输出堆栈与内部路径（`EVID_NODE_CFG_ERR_HANDLER`）
- `koa-static` 根目录来源可控或启用 `index`/`hidden` 暴露目录，且存在可访问 URL（`EVID_NODE_CFG_SECURITY_SWITCH`）
- `@koa/cors` 通配 + `credentials` 组合，且存在携带 Cookie 的受保护接口（`EVID_NODE_CFG_SECURITY_SWITCH`）
- body 解析器未挂载或未设 `limit`，而 handler 直接消费 `ctx.request.body`（静默 undefined 透传 / 超大请求体进入解析）（`EVID_NODE_CFG_RUNTIME_SETTING`；koa-body multipart 配置面见 `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`）

### ⚠️待验证

- 洋葱链覆盖范围不清：鉴权中间件存在条件短路分支（未统一 `await next()`），静态无法确认全部路径
- `ctx.ip`/限流依赖部署环境（反向代理是否透传来源 IP），静态无法确认
- `koa-session` 的 `signed`/`cookie.secure` 在生产分支（HTTPS 条件）下才启用，静态无法确认部署环境
- 错误响应是否泄露堆栈取决于 `NODE_ENV` 运行时值，静态无法确认

### 误报

- 鉴权中间件为洋葱最外层且无条件 `await next()` 放行，未鉴权直接拒绝
- 自定义 `app.on('error')`/错误中间件已注册且响应已净化（无堆栈/内部路径）
- CORS 未通配或未携带 `credentials`，helmet/koa-helmet 全挂载点启用
- `koa-static` 根目录硬编码固定、`index: false` 且置于鉴权之后

## 测试建议（强制）

### 正向测试

- 无鉴权直接请求受保护路由 → 应被拒绝（401/403），验证洋葱链覆盖
- 构造超限 body / 超限 multipart 请求 → 应返回 413/400 而非进入 handler
- 触发异常请求 → 响应应为净化错误页，不包含堆栈/内部路径
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 合法请求完整通过洋葱链（鉴权 + 限流 + 解析）正常返回
- 正常范围内 body/上传请求可用，未被误拒
- 生产模式（`NODE_ENV=production`）下错误响应不泄露堆栈

### 回归测试

- 洋葱层注册顺序变更后重验鉴权覆盖与静态目录位置
- 新增路由必须纳入鉴权覆盖清单后复测
- 错误处理/body 解析器改动后复测堆栈泄露与 413 行为

## 证据引用

- `EVID_NODE_CFG_MIDDLEWARE_ORDER`
- `EVID_NODE_CFG_ERR_HANDLER`
- `EVID_NODE_CFG_SECURITY_SWITCH`
- `EVID_NODE_CFG_RUNTIME_SETTING`
- `EVID_NODE_SESS_COOKIE_FLAGS`（koa-session 配置面联调 node-session-cookie-audit）
- `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`（koa-body multipart 配置面联调 node-file-upload-audit）

## 输出

- `node/framework_audit/koa_{timestamp}.md`
- 必须写明：洋葱中间件链注册顺序与短路条件、ctx 数据绑定与 `ctx.state` 注入面、静态目录暴露面、运行时配置（body limit/session/CORS）、鉴权覆盖范围与未覆盖路由
- 必须写明环境差异：`NODE_ENV` 分支、`ctx.ip` 反代依赖、生产/开发配置差异
- 消费关系：影响漏洞强结论时必须显式写明如何被 `node/route_tracer`、各 `node-vuln-audit` 专项（xss/session-cookie/file-upload 等）与 `node-audit-pipeline` 消费
