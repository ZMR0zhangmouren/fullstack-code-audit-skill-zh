---
name: node-nuxt-audit
description: Node.js Nuxt.js 框架专项审计工具。针对 Nuxt 3 的文件约定入口、Nitro server 路由、serverMiddleware/routeRules 控制面、SSR 注水面与运行时配置进行白盒审计。
---

# Nuxt.js 框架专项审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 Nuxt 相关的入口定义（`pages/` 文件约定、Nitro `server/api` 路由、serverMiddleware）、`nuxt.config` 配置面（routeRules/auth）、SSR 注水、useFetch/useAsyncData 数据流与运行时配置抓手
- 若项目存在插件/中间件二次封装、统一鉴权包装层、自定义 Nitro handler 工厂，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐 `server/api/*` 与 `pages/` 入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（本专项核心输入：确认 serverMiddleware 与路由中间件覆盖顺序）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于对齐匿名入口、P0/P1 分桶与鉴权覆盖范围，含 Nitro 路由内鉴权与 auth 模块配置）
- 可选：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`（用于将注水数据、useFetch 数据流与具体入口、副作用链交叉引用）
- 可选：`node/vuln_audit/*_{timestamp}.md`（用于与 xss/session-cookie/file-upload 等漏洞专项互相印证）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于对齐 SSR 注水、BFF 转发或前后端同构参数来源）

## 重点检查

- `nuxt.config` 的 `serverMiddleware`/`routeRules` 配置：routeRules 缓存策略将敏感数据/鉴权响应缓存公开
- Nitro `server/api/*` 路由 handler 内参数绑定与鉴权缺失（框架不默认鉴权，逐 handler 需显式校验）
- `useFetch`/`useAsyncData` SSR 数据流：服务端拉取敏感数据原样进入客户端 payload
- `__NUXT__` 注水数据含敏感信息或未净化 HTML → 注水注入面（联调 node-xss-audit 的 EVID_NODE_XSS_SSR_HYDRATION）
- 中间件/插件执行顺序：路由中间件（`middleware/`）与 Nitro server middleware 的执行时机与短路条件
- auth 模块配置：`@nuxtjs/auth`/`nuxt-auth-utils` 等模块的 cookie/secret 配置与登录后票据处理
- 服务端 `server/api` 与客户端组件数据边界：客户端直接请求未净化接口、`$fetch` 直通后端

## 枚举规则（强制细化）

### 1. 框架边界层

- 枚举入口定义方式：`pages/` 文件约定（页面路由）、`server/api/*` 文件约定（Nitro 路由 handler）、`server/routes/*`、`serverMiddleware` 数组配置（nuxt.config）
- 枚举路由中间件：`middleware/` 目录文件与 `definePageMeta({ middleware })`/`defineNuxtRouteMiddleware` 挂载点、命名中间件执行顺序（全局/局部）
- 枚举 `nuxt.config` 的 `routeRules`：每条规则的 `swr`/`isr`/`redirect`/`proxy`/`cors` 配置、路径匹配面与缓存语义（缓存敏感数据泄露线索）
- 识别请求生命周期边界：request → nitro server middleware → handler → SSR 页面数据 → `__NUXT__` 注水 → 浏览器
- 识别插件执行顺序：`plugins/` 目录插件与 `app.vue`/`app.config` 初始化链

### 2. 运行时配置层

- 枚举 SSR 渲染模式：`ssr: true/false`、`useFetch`/`useAsyncData` 服务端数据拉取点与 `key` 复用、`payload` 传递面
- 枚举注水数据面：`__NUXT__` JSON（useState/useFetch 结果入 payload）、`dangerouslySetInnerHTML`/`v-html` 使用点（联调 node-xss-audit 的 `EVID_NODE_XSS_SSR_HYDRATION`）
- 枚举环境变量读取点：`process.env`、`runtimeConfig`（`public` vs `private` 字段）、`.env*` 文件内容与敏感项（secret、DB 连接串）
- 枚举 `nuxt.config` 的 `runtimeConfig` 边界：public 字段进客户端 bundle、private 字段仅服务端可见的配置面
- 枚举 Nitro 配置面：`nitro.routeRules`、`nitro.prerender`、`nitro.output` 部署形态（node-server/vercel/edge）

### 3. 前置控制面层

- 枚举鉴权覆盖范围：`@nuxtjs/auth`/`nuxt-auth-utils` 模块配置（session/cookie/secret）、Nitro handler 内显式鉴权逻辑（`getCookie`/`jwt.verify`）、路由中间件内鉴权（`defineNuxtRouteMiddleware`）
- 识别 Nitro 路由鉴权缺失：逐 handler 比对是否调用鉴权逻辑，标记未覆盖的 `server/api/*` 入口
- 枚举 serverMiddleware 执行顺序：与 `server/api` 路由的相对顺序、条件放行分支（`next()` 未统一调用）
- 枚举 CORS 与缓存控制面：`routeRules.cors` 配置、`Access-Control-Allow-Origin` 通配 + `credentials`、敏感响应的 `Cache-Control` 头

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| serverMiddleware 鉴权 | `serverMiddleware: [{ path: '/api', handler: authHandler }]` | 检查 serverMiddleware 相对 `server/api` 路由的执行顺序与条件放行分支 | 鉴权先于受保护 handler 且 fail-close → ✅ 安全；serverMiddleware 挂于路由之后或条件放行 → 🔴 高危 |
| 注水净化 | useState/useFetch 数据经序列化进入 `__NUXT__` payload | 检查注水数据是否含敏感信息（token/内部路径/用户数据原样），`v-html` 输出点是否净化 | 注水数据最小化且输出净化 → ✅ 安全；敏感数据入注水或未净化输出 → 🔴 高危（联调 xss 专项） |
| Nitro 路由鉴权 | handler 内显式 `getCookie`/`jwt.verify` 校验 | 逐 `server/api/*` handler 检查鉴权调用链（含共享 helper 的真实调用） | 所有可达 handler fail-close → ✅ 安全；存在无鉴权可达 handler → 🔴 高危 |
| routeRules 缓存策略 | `routeRules: { '/api/profile': { swr: 3600 } }` | 检查缓存规则是否命中含敏感数据的接口/页面（用户级数据、鉴权响应） | 敏感面未缓存或缓存键隔离用户 → ✅ 安全；用户级/鉴权数据被公共缓存 → 🔴 高危 |

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

- `EVID_NODE_CFG_SSR_MODE` 显示 `__NUXT__` 注水/useFetch payload 含敏感数据或未净化 HTML 输出，且入口可达（联调 xss 专项 `EVID_NODE_XSS_SSR_HYDRATION`）
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` 显示 serverMiddleware/路由中间件位于受保护 handler 之后或条件放行，且存在无鉴权可达的 `server/api` 入口
- `EVID_NODE_CFG_SECURITY_SWITCH` 显示 routeRules 对用户级/鉴权数据接口配置 `swr`/`isr` 公共缓存，或 CORS 通配 + `credentials` 组合且存在携带 Cookie 的受保护接口
- `EVID_NODE_CFG_RUNTIME_SETTING` 显示 `runtimeConfig.public` 或 `NUXT_PUBLIC_` 类前缀字段存放密钥/内部地址，且进入客户端 bundle
- Nitro handler 内参数绑定后直接进入 sink 且无净化/校验 → 与对应漏洞专项（nosql/cmd/ssrf）联动确认

### ⚠️待验证

- serverMiddleware 存在条件性放行分支，静态无法确认全部路径行为（`EVID_NODE_CFG_MIDDLEWARE_ORDER`）
- routeRules 缓存是否真正缓存敏感响应取决于 CDN/部署层行为与缓存键设计，需结合部署环境确认
- auth 模块（`@nuxtjs/auth` 等）的 cookie/secret 配置依赖版本行为，静态无法确认全部会话面（`EVID_NODE_SESS_COOKIE_FLAGS`）
- `useFetch` 服务端数据是否被 XSS 利用取决于前端输出上下文，需与 xss 专项联合确认

### 误报

- serverMiddleware 全局先于所有受保护 handler 且 fail-close（未鉴权直接拒绝）
- `__NUXT__` 注水仅含公开数据且输出经框架默认转义（无 `v-html`/`dangerouslySetInnerHTML`）
- routeRules 缓存仅作用于静态公开页面且缓存键按用户隔离，敏感数据不入公共缓存
- `runtimeConfig.private` 字段正确放置且未进入客户端 bundle

## 测试建议（强制）

### 正向测试

- 构造绕过 serverMiddleware 的路径请求受保护 `server/api` handler → 应被拒绝（401/403）
- 请求含敏感数据的 SSR 页面 → 检查 `__NUXT__` payload 与 HTML 是否含敏感信息或未净化输出
- 连续请求配置了 swr 缓存且含用户数据的接口 → 验证不同用户响应是否被公共缓存串用
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 合法请求携带有效 session/cookie 通过中间件正常进入受保护页面/handler
- 正常 SSR 页面注水数据完整且不含敏感字段，前端正常水合
- 静态公开页面的 routeRules 缓存正常工作，无数据串用

### 回归测试

- 中间件顺序或 serverMiddleware 配置变更后重验鉴权覆盖
- 新增 `server/api/*` handler 必须纳入鉴权覆盖清单后复测
- `nuxt.config` routeRules/runtimeConfig 改动后复测缓存泄露与配置泄露面

## 证据引用

- `EVID_NODE_CFG_SSR_MODE`（SSR 渲染模式与 `__NUXT__` 注水面配置证据）
- `EVID_NODE_CFG_MIDDLEWARE_ORDER`（serverMiddleware/路由中间件顺序与短路条件证据）
- `EVID_NODE_CFG_SECURITY_SWITCH`（routeRules 缓存策略与 CORS 配置证据）
- `EVID_NODE_CFG_RUNTIME_SETTING`（runtimeConfig/环境变量可见面证据）
- `EVID_NODE_XSS_SSR_HYDRATION`（`__NUXT__` 注水注入面，联调 node-xss-audit）
- `EVID_NODE_SESS_COOKIE_FLAGS`（auth 模块 session/cookie 配置面，联调 node-session-cookie-audit）
- `EVID_NODE_SSTI_RENDER_POINT`（自定义渲染/模板引擎渲染面，如集成的模板引擎或自定义 Nitro 渲染，联调 node-ssti-audit；常规 SSR 无模板引擎面，属低优先）

## 输出

- `node/framework_audit/nuxt_{timestamp}.md`
- 必须写明：入口类型与挂载方式（`pages/` 与 `server/api/*` 文件约定、serverMiddleware）、中间件执行顺序与短路条件、SSR 注水面（`__NUXT__`/useFetch payload）、routeRules 缓存策略与敏感面、runtimeConfig 边界、auth 模块配置
- 必须写明环境差异：`ssr` 开关分支、Nitro 部署形态（node-server/vercel/edge）差异、开发/生产配置差异
- 消费关系：影响漏洞强结论时必须显式写明如何被 `node/route_tracer`、各 `node-vuln-audit` 专项（xss/session-cookie/nosql/ssrf 等）与 `node-audit-pipeline` 消费
