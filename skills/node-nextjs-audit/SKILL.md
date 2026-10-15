---
name: node-nextjs-audit
description: Node.js Next.js 框架专项审计工具。针对 Next.js 应用的 App/Pages Router 入口面、middleware 控制面、SSR 注水面、图像优化与运行时配置进行白盒审计。
---

# Next.js 框架专项审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 Next.js 相关的入口定义（app/ 与 pages/ 文件约定、API Routes/Route Handlers）、middleware matcher、rewrites/redirects、SSR 注水、环境变量与图像优化配置抓手
- 若项目存在自定义 Server（custom server 改写 getServerSideProps/中间件）、二次封装的数据获取 hook、统一鉴权包装层，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐 pages/api 与 app/api 入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（本专项核心输入：确认 middleware.ts 覆盖范围与 matcher 生效面）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于对齐匿名入口、P0/P1 分桶与鉴权覆盖范围，含 middleware 内 cookie 校验与 API 路由内鉴权）
- 可选：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`（用于将注水数据、next/image 远程源与具体入口、副作用链交叉引用）
- 可选：`node/vuln_audit/*_{timestamp}.md`（用于与 xss/ssrf/open-redirect/session-cookie 等漏洞专项互相印证）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于对齐 SSR 注水、BFF 转发或前后端同构参数来源）

## 重点检查

- `middleware.ts` 未配置 `matcher`：未配 matcher 时 middleware 全量拦截或全量放行的二义，以及 matcher 遗漏受保护路径（跳过鉴权的可达入口）
- `next.config.js` 的 `rewrites`/`redirects` 目标含用户可控片段 → 开放重定向/SSRF 线索（联调 node-open-redirect/node-ssrf 专项）
- API Routes（`pages/api`）与 Route Handlers（`app/api`）内鉴权缺失：路由级无鉴权、依赖前端隐藏入口
- `__NEXT_DATA__`/RSC 注水数据含敏感信息或未净化 HTML → 注水注入面（联调 node-xss-audit 的 EVID_NODE_XSS_SSR_HYDRATION）
- `NEXT_PUBLIC_*` 前缀环境变量误放密钥/内部地址 → 浏览器 bundle 与源码可见泄露
- `next/image` 远程源未配置 `remotePatterns` 白名单或配置过宽 → 图像优化代理 SSRF 线索
- 服务端组件 vs 客户端组件边界：`'use client'` 内放置敏感逻辑（密钥、鉴权判断）导致前端暴露
- edge runtime 权限面：middleware/edge 函数内处理敏感操作或依赖不可信环境变量

## 枚举规则（强制细化）

### 1. 框架边界层

- 枚举入口定义方式：`app/` 目录文件约定（`page.tsx`/`layout.tsx`/`route.ts`/`middleware.ts`）与 `pages/` 目录约定（`pages/api/*` API Routes、`getServerSideProps`/`getStaticProps` 文件导出）
- 枚举 `middleware.ts`（或 `middleware.js`）的 `export default` 逻辑与 `matcher` 配置：未配 matcher、matcher 数组遗漏的路径前缀、matcher 使用正则的边界
- 枚举 `next.config.js` 的 `rewrites`/`redirects` 配置：目标来源（硬编码/环境变量/用户输入）、`has`/`missing` 条件、通配符匹配面
- 枚举服务端组件 vs 客户端组件边界：`'use client'` 指令文件、`use server`/Server Actions 暴露面、RSC 数据序列化面（非序列化对象/函数透传）
- 识别请求生命周期边界：request → middleware → route handler/page → 注水 payload → 浏览器

### 2. 运行时配置层

- 枚举 SSR 渲染模式：`getServerSideProps`/`getStaticProps`/`getInitialProps`、`generateStaticParams`、`output: 'standalone'`、ISR（`revalidate`）配置
- 枚举注水数据面：`__NEXT_DATA__` JSON、RSC payload、`dangerouslySetInnerHTML` 使用点、服务端数据未净化直接注入 HTML（联调 node-xss-audit 的 `EVID_NODE_XSS_SSR_HYDRATION`）
- 枚举环境变量读取点：`process.env`、`NEXT_PUBLIC_` 前缀变量（浏览器侧可见）、`.env*` 文件内容与敏感项（secret、token、DB 连接串）
- 枚举图像优化配置：`next/image` 的 `remotePatterns`/`domains`、`loader` 自定义配置、图像请求转发面（SSRF 线索，联调 node-ssrf-audit）
- 枚举 edge runtime：`export const runtime = 'edge'` 的入口/中间件、edge 环境变量可见面与权限放大面

### 3. 前置控制面层

- 枚举鉴权覆盖范围：middleware 中 cookie/token 校验（`cookies()`/`req.cookies`、jwt.verify）、API Route 内鉴权逻辑是逐路由还是共享 helper、`@auth`/NextAuth 配置
- 识别 API Route/Route Handler 鉴权缺失：比对路由清单与鉴权逻辑覆盖，标记未覆盖的 `pages/api/*` 与 `app/api/*` 入口
- 枚举 CORS 配置：`headers()` 动态响应头、`next.config` `headers` 静态配置、`Access-Control-Allow-Origin` 通配 + `credentials` 组合
- 枚举 Server Actions 暴露面：`'use server'` 导出的动作是否绕过前端鉴权、参数校验缺失

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| middleware matcher 覆盖 | `export const config = { matcher: ['/api/:path*', '/dashboard/:path*'] }` | 检查 matcher 是否覆盖全部受保护入口，未配 matcher 时确认 middleware 全局生效意图；比对 matcher 表达式与路由清单 | matcher 覆盖全部受保护面且逻辑 fail-close → ✅ 安全；matcher 遗漏路径或未配 matcher 造成鉴权二义 → 🔴 高危 |
| SSR 注水净化 | 服务端数据经序列化进入 `__NEXT_DATA__`/RSC payload | 检查注水数据是否含敏感信息（token/内部路径/用户数据原样），HTML 输出点是否净化 | 注水数据最小化且 HTML 输出净化 → ✅ 安全；敏感数据入注水或未净化输出 → 🔴 高危（联调 xss 专项） |
| API Route 鉴权 | API Routes/Route Handlers 内显式调用鉴权 helper | 逐入口检查 `pages/api` 与 `app/api` 是否调用鉴权逻辑（含共享 helper 的真实调用链） | 所有可达入口 fail-close → ✅ 安全；存在无鉴权可达入口 → 🔴 高危 |
| 图像远程源白名单 | `next.config` 中 `images.remotePatterns` 显式声明 | 检查 `next/image` 使用点与 `remotePatterns` 配置，确认远程源是否被白名单约束 | 白名单固定且协议/主机收紧 → ✅ 安全；未配白名单或通配过宽 → ⚠️ 待确认（SSRF 线索） |

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

- `EVID_NODE_CFG_SSR_MODE` 显示 SSR/注水面（`__NEXT_DATA__`/RSC payload）存在敏感数据入注水或未净化 HTML 输出，且入口可达（联调 xss 专项 `EVID_NODE_XSS_SSR_HYDRATION`）
- `EVID_NODE_CFG_MIDDLEWARE_ORDER` 显示 `middleware.ts` 未配 matcher 或 matcher 遗漏受保护路径，且存在无鉴权的可达 API 入口（配置缺失 + 入口可达）
- `EVID_NODE_CFG_RUNTIME_SETTING` 显示 `NEXT_PUBLIC_*` 前缀下存放密钥/内部地址，且被组件或客户端代码引用
- `next/image` 远程源未配置 `remotePatterns` 或配置通配过宽，且存在用户可控图像 URL 输入点（`EVID_NODE_SSRF_URL_CONSTRUCTION`）
- `rewrites`/`redirects` 目标含用户可控片段且无目标校验 → 开放重定向/SSRF 线索（`EVID_NODE_CFG_SECURITY_SWITCH`）

### ⚠️待验证

- middleware 鉴权存在条件性放行分支（cookie 缺失走默认页而非拒绝），静态无法确认全部路径行为（`EVID_NODE_CFG_MIDDLEWARE_ORDER`）
- `next/image` 远程源是否真正可被攻击者控制取决于图像 URL 上游来源，需 trace 确认
- Server Actions（`'use server'`）的参数校验依赖运行时框架行为，静态无法确认全部校验缺失
- 注水数据是否被 XSS 利用取决于前端输出上下文（`dangerouslySetInnerHTML` vs 安全插值），需与 xss 专项联合确认

### 误报

- `middleware.ts` matcher 已显式覆盖全部受保护入口且鉴权逻辑 fail-close（未通过即拒绝）
- 注水数据仅含公开数据且 HTML 输出均经框架默认转义（无 `dangerouslySetInnerHTML`）
- `NEXT_PUBLIC_*` 仅含非敏感公开配置（如站点名、公开 API 端点），无密钥/内部信息
- `next/image` `remotePatterns` 已固定白名单且协议/主机收紧，图像 URL 无可控输入点（`EVID_NODE_SSRF_ALLOWLIST`）

## 测试建议（强制）

### 正向测试

- 构造绕过 matcher 的路径（如大小写、尾斜杠、双重编码）请求受保护 API → 应被拒绝（401/403）
- 请求含敏感数据的 SSR 页面 → 检查注水 payload 与 HTML 是否含敏感信息或未净化输出
- 构造恶意 `?url=` 触发 `next/image` 代理 → 应被白名单拒绝而非发起请求
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 合法请求携带有效 cookie/token 通过 middleware 正常进入受保护页面/API
- 正常 SSR 页面注水数据完整且不含敏感字段，前端正常水合
- 白名单内图像源正常加载，无代理误拒绝

### 回归测试

- matcher 新增/变更路径后重验鉴权覆盖与绕过面
- 新增 API Route/Route Handler 必须纳入鉴权覆盖清单后复测
- `next.config`（rewrites/redirects/images）改动后复测开放重定向与图像 SSRF 面

## 证据引用

- `EVID_NODE_CFG_SSR_MODE`（SSR 渲染模式与注水面配置证据）
- `EVID_NODE_CFG_MIDDLEWARE_ORDER`（middleware matcher 与中间件顺序证据）
- `EVID_NODE_CFG_RUNTIME_SETTING`（NEXT_PUBLIC_ 环境变量与运行时配置证据）
- `EVID_NODE_CFG_SECURITY_SWITCH`（CORS 通配+credentials、rewrites 目标校验开关证据）
- `EVID_NODE_XSS_SSR_HYDRATION`（`__NEXT_DATA__`/RSC 注水注入面，联调 node-xss-audit）
- `EVID_NODE_SSRF_URL_CONSTRUCTION` 与 `EVID_NODE_SSRF_ALLOWLIST`（next/image 远程源与图像代理 SSRF 面，联调 node-ssrf-audit）
- `EVID_NODE_SSTI_RENDER_POINT`（自定义渲染/模板引擎渲染面，如 custom server 或动态模板输出，联调 node-ssti-audit；常规 SSR 无模板引擎面，属低优先）

## 输出

- `node/framework_audit/nextjs_{timestamp}.md`
- 必须写明：入口类型与挂载方式（app/ 与 pages/ 文件约定、API Routes/Route Handlers、middleware）、matcher 覆盖范围与未覆盖入口、SSR 注水面（`__NEXT_DATA__`/RSC）、rewrites/redirects 目标来源、NEXT_PUBLIC_ 泄露项、next/image 远程源配置、edge runtime 暴露面
- 必须写明环境差异：开发/生产构建差异（`NODE_ENV` 分支）、`output: 'standalone'` 部署形态、ISR 缓存行为
- 消费关系：影响漏洞强结论时必须显式写明如何被 `node/route_tracer`、各 `node-vuln-audit` 专项（xss/ssrf/open-redirect/session-cookie 等）与 `node-audit-pipeline` 消费
