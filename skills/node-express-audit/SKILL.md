---
name: node-express-audit
description: Node.js Express 框架专项审计工具。针对 Express 应用的入口注册、中间件链、静态目录与运行时配置的框架边界、运行时配置与控制面进行白盒审计。
---

# Express 框架专项审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 Express 相关的入口定义（app / express.Router 注册）、中间件链顺序、静态目录、解析器、会话与安全头配置抓手
- 若项目存在 createApp()、中间件组合器、路由工厂等 Express 二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（本专项核心输入：确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于对齐匿名入口、P0/P1 分桶与鉴权覆盖范围）
- 可选：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`（用于将中间件/解析器风险与具体入口、副作用链交叉引用）
- 可选：`node/vuln_audit/*_{timestamp}.md`（用于与 ssti/xss/session-cookie 等漏洞专项互相印证）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于对齐 SSR、BFF 转发或前后端同构参数来源）

## 重点检查

- 中间件链顺序缺陷：鉴权/安全中间件注册在路由之后、静态目录或敏感路由先于鉴权执行
- 错误中间件缺失或未用 4 参数签名：Express 默认错误处理器在非生产环境输出堆栈与内部路径（fail-open）
- `express.static` 根目录可控、启用 `dotfiles`/目录列表或置于鉴权之前 → 任意文件读取/目录暴露
- `express.json` / `express.urlencoded` 未配置 `limit`/`type` → 超大请求体或错误 Content-Type 解析面
- `trust proxy` 配置过宽 → `req.ip` 可伪造，绕过 IP 白名单与速率限制
- view engine（ejs/pug/handlebars）渲染用户可控模板或未转义数据 → 联调 node-ssti-audit
- helmet 缺失、CORS 通配 + `credentials` 组合 → 安全头缺失/任意来源跨域
- 路由级鉴权缺失：passport/express-jwt 未覆盖部分 router 或动态注册路由

## 枚举规则（强制细化）

### 1. 框架边界层

- 枚举入口定义方式：`app.get/post/put/delete/all`、`app.use`、`express.Router()` 及 `router.get/post/use`、动态路由注册（`forEach`/循环 `app.use`、`app.use(router)` 挂载、`app.all('*')` 兜底）
- 枚举中间件链顺序与短路条件：按注册顺序记录 `app.use` 链，`next()` 是否被调用、条件性放行分支、`res.end()`/`res.send()` 后的链中断点
- 枚举静态目录：`express.static(root, options)` 的 `root` 来源（硬编码/环境变量/用户输入）、`dotfiles`、`index`、`serve-index` 中间件、相对鉴权中间件的位置
- 识别请求生命周期边界：req → middleware → handler → response，标注直接 `res.send` 拼接输出点（供 XSS 专项）
- 识别框架默认行为：404 兜底、默认错误处理（堆栈泄露面）、`NODE_ENV` 分支行为

### 2. 运行时配置层

- 枚举 `process.env`、`dotenv`、`.env` 读取点与敏感项（secret、token、DB 连接串）
- 枚举 body 解析配置：`express.json({ limit, type })`、`express.urlencoded`、`raw`/`text` 解析器
- 枚举 `app.set('trust proxy', ...)` 配置值与 `req.ip`/`req.ips` 使用点
- 枚举 view engine：`app.set('view engine')`、`app.set('views')`、`res.render` 调用点（联调 node-ssti-audit）
- 枚举会话与 Cookie 配置：`express-session`（`secret`/`cookie` 选项/`name`）、`cookie-parser`（`signed` 密钥）
- 枚举安全头与跨域配置：helmet、`cors({ origin, credentials })`、CSP、HSTS
- 若存在 createApp()、中间件组合器、路由工厂等二次封装，必须逐层展开到真实 `app.use`/路由调用点

### 3. 前置控制面层

- 枚举鉴权覆盖范围：`passport.initialize()`/`passport.authenticate`、`express-jwt`、自定义 auth 中间件是全局 `app.use` 还是仅部分路由挂载
- 识别路由级鉴权缺失：比对路由清单与鉴权中间件覆盖，标记未覆盖 router 与动态注册路由
- 枚举速率限制：`express-rate-limit` 配置、与 `trust proxy` 的联动（IP 伪造绕过限流）
- 枚举请求大小限制：body `limit`、multer 等上传中间件的 `limits`/`fileFilter`

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 中间件顺序 | `app.use(auth)` 先于 `app.use(routes)` 注册 | 按注册顺序逐条列出中间件，检查鉴权/安全中间件相对路由与静态目录的位置及短路条件 | 鉴权先于受保护面且无条件放行 → ✅ 安全；鉴权挂于路由之后或条件性放行 → 🔴 高危 |
| 解析器限制 | `express.json({ limit: '1mb', type: 'application/json' })` | 检查 body 解析器 `limit`/`type` 配置与挂载点 | 明确 `limit` 且 `type` 收紧 → ✅ 安全；未配置 `limit` 或 `type: '*/*'` → ⚠️ 待确认 |
| 鉴权覆盖 | `app.use(requireAuth)` 或逐路由 `authMiddleware` | 比对路由/中间件清单与鉴权覆盖范围，含动态注册路由 | 全局或逐路由 fail-close → ✅ 安全；存在可达的无鉴权路由 → 🔴 高危 |
| 错误处理 | `app.use((err, req, res, next) => ...)` 4 参数签名 | 检查是否注册 4 参数错误中间件及响应内容是否含堆栈/内部路径 | 自定义错误中间件且响应净化 → ✅ 安全；缺失或非 4 参数签名 → 🔴 默认堆栈泄露（fail-open） |
| 静态目录暴露 | `express.static(path.join(__dirname, 'public'))` | 检查 `root` 来源、`dotfiles`/`index` 选项、相对鉴权中间件的位置 | `root` 固定且无目录列表且置于鉴权后 → ✅ 安全；`root` 可控或目录暴露 → 🔴 高危 |

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

- `EVID_NODE_CFG_MIDDLEWARE_ORDER` 显示鉴权中间件位于路由/静态目录之后，且受保护入口可达（配置缺失 + 入口可达）
- 4 参数错误中间件缺失，`NODE_ENV !== 'production'` 时默认错误响应输出堆栈与内部路径（`EVID_NODE_CFG_ERR_HANDLER`）
- `express.static` 根目录来源可控或暴露敏感目录，且存在可访问 URL（`EVID_NODE_CFG_SECURITY_SWITCH`）
- CORS 通配 + `credentials: true` 组合，且存在携带 Cookie 的受保护接口（`EVID_NODE_CFG_SECURITY_SWITCH`）
- body 解析器未设 `limit` 且入口可达，存在超大请求/异常 Content-Type 处理路径（`EVID_NODE_CFG_RUNTIME_SETTING`）

### ⚠️待验证

- 中间件覆盖范围不清：鉴权中间件存在条件性放行分支（`next()` 未统一调用），静态无法确认全部路径
- `trust proxy` 依赖部署环境（反向代理是否设置 `X-Forwarded-For`），静态无法确认 `req.ip` 可信度
- helmet 仅在入口 app.js 启用，但存在子应用挂载/二次封装的独立实例无法静态确认
- 错误响应是否泄露堆栈取决于运行时 `NODE_ENV` 值，静态无法确认部署环境

### 误报

- 鉴权中间件全局 `app.use` 于所有路由之前且 fail-close（未鉴权直接拒绝）
- 4 参数错误中间件已注册且响应内容已净化（无堆栈/内部路径）
- helmet 全挂载点启用，CORS 未通配或未携带 `credentials`
- `express.static` 根目录硬编码固定且置于鉴权之后

## 测试建议（强制）

### 正向测试

- 无鉴权直接请求受保护路由 → 应被拒绝（401/403），验证鉴权覆盖
- 构造超限 body（超过 `limit`）请求 → 应返回 413 而非进入 handler
- 触发异常请求 → 响应应为净化错误页，不包含堆栈/内部路径
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 合法请求完整通过中间件链（鉴权 + 限流 + 解析）正常返回
- 正常范围内 body/上传请求可用，未被误拒
- 生产模式（`NODE_ENV=production`）下错误响应不泄露堆栈

### 回归测试

- 中间件顺序变更后重验鉴权覆盖与静态目录位置
- 新增路由必须纳入鉴权覆盖清单后复测
- 错误中间件/body 解析器改动后复测堆栈泄露与 413 行为

## 证据引用

- `EVID_NODE_CFG_MIDDLEWARE_ORDER`
- `EVID_NODE_CFG_SECURITY_SWITCH`
- `EVID_NODE_CFG_ERR_HANDLER`
- `EVID_NODE_CFG_RUNTIME_SETTING`
- `EVID_NODE_SESS_COOKIE_FLAGS`（express-session/cookie-parser 配置面联调 node-session-cookie-audit）
- `EVID_NODE_SSTI_RENDER_POINT`（view engine 渲染面联调 node-ssti-audit）

## 输出

- `node/framework_audit/express_{timestamp}.md`
- 必须写明：入口类型与挂载方式（app/router/动态注册）、中间件链顺序与短路条件、静态目录暴露面、运行时配置（body limit/trust proxy/session/CORS/view engine）、鉴权覆盖范围与未覆盖路由
- 必须写明环境差异：`NODE_ENV` 分支、`trust proxy` 部署依赖、生产/开发配置差异
- 消费关系：影响漏洞强结论时必须显式写明如何被 `node/route_tracer`、各 `node-vuln-audit` 专项（ssti/xss/session-cookie/file-upload 等）与 `node-audit-pipeline` 消费
