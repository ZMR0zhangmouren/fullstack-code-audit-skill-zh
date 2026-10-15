---
name: node-config-audit
description: Node.js 配置安全审计工具。识别 helmet 缺失、CORS 通配+credentials、trust proxy 过宽、.env 硬编码 secret 与生产环境明细错误页风险，输出分级、证据和修复建议。
---

# Node.js 配置安全审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与框架入口配置、安全中间件、环境变量、安全开关相关的共享抓手
- 若项目存在 setupSecurity、applyMiddleware、config/index.js、env.js 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **静态证据驱动**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致
- 职责边界：会话、Cookie、JWT 会话配置细节归 `node-session-cookie-audit`，本专项管框架与运行时配置面

## 重点检查

- helmet 缺失或仅局部挂载：CSP、HSTS、X-Frame-Options 等安全头缺省
- `cors({ origin: '*', credentials: true })` 危险组合；origin 回显 + credentials 反射任意域
- `app.set('trust proxy', true)` 过宽：`req.ip` 可被 `X-Forwarded-For` 伪造，影响限流与审计归因
- `.env` 入仓、源码硬编码 secret、dotenv 生产加载开发默认值
- `NODE_ENV !== 'production'` 时 express 默认错误页输出堆栈；调试开关、Swagger/OpenAPI、GraphQL Playground、pino-pretty 诊断面生产暴露
- `next.config`（devIndicators、source maps、headers）与 `nuxt.config`（devtools、ssr）的生产安全开关
- NestJS `ConfigModule.forRoot` 默认值与失效的环境分支判断

## 枚举规则（强制细化）

- 枚举框架入口与配置文件：`app.js` / `server.js` / `main.ts` / `config/` / `.env*` / `next.config.*` / `nuxt.config.*`
- rg 搜索：`helmet`、`cors(`、`origin`、`credentials`、`trust proxy`、`dotenv`、`process.env`、`NODE_ENV`、`app.set(`、`swagger`、`playground`、`devtools`、`devtool`、`sourcemap`
- 对每个配置点记录：配置位置、运行时代码、影响面、环境限定条件（NODE_ENV 分支）、是否属于安全开关
- 核对中间件挂载顺序：helmet / cors / rate limit 是否在路由之前全局生效，是否存在路由级覆盖
- 识别环境变量回退默认值：`process.env.X || 'dev-secret'` 形式的 fail-open 写法
- 若配置经二次封装（config 中间层），必须逐层展开到真实生效值

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 环境分支 | `process.env.NODE_ENV` 判断 | 确认危险配置是否被生产条件严格限定 | 仅 development 生效且默认拒绝 → ✅ 安全；判断缺失或反转 → 🔴 高危 |
| 安全中间件 | helmet / cors / rate limit | 核对挂载顺序与参数（origin 白名单、credentials） | 全局挂载且 CORS 收敛 → ✅ 安全；`origin:'*'` + `credentials:true` → 🔴 高危 |
| 代理信任 | `app.set('trust proxy', N)` | 核对信任跳数与真实代理拓扑 | 指定跳数或可信网段 → ✅ 安全；`true` 全信任 → 🔴 高危 |
| secret 来源 | dotenv / 环境注入 / 密钥管理服务 | 追踪 secret 声明位置与默认回退值 | 环境注入且无弱默认 → ✅ 安全；源码字面量或 .env 入仓 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：危险配置开关疑似在非开发环境生效，或安全中间件缺失影响敏感端点
- `待确认`：上下文显示可疑模式，但外部输入来源、barrier 行为或调用链不清晰
- `误报`：输入来自固定常量 / 枚举映射，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到外部可控输入进入 Sink 位的证据 → `确认漏洞`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_CFG_SECURITY_SWITCH` + `EVID_NODE_CFG_RUNTIME_SETTING`：`cors({ origin: '*', credentials: true })` 生效或 helmet 缺失且生产无替代安全头
- `EVID_NODE_CFG_ERR_HANDLER`：非生产环境输出明细错误页，堆栈与内部路径返回客户端
- `EVID_NODE_CFG_RUNTIME_SETTING`：`.env` 入仓或源码硬编码 secret，且无环境隔离与轮换
- `EVID_NODE_CFG_MIDDLEWARE_ORDER`：`trust proxy` 过宽导致 `req.ip` 可伪造并影响限流、审计归因

### ⚠️待验证

- 命中 helmet / cors 配置点，但生产部署形态（反向代理是否补齐安全头）不明
- `.env` 文件存在，但无法确认是否入仓、CI 是否注入真实值
- `next.config` / `nuxt.config` 安全开关命中，但渲染模式与部署目标未确认

### 误报

- 危险配置仅在 `NODE_ENV=development` 分支生效，生产默认 fail-close
- helmet 全局挂载、CORS 白名单收敛、secret 由环境或密钥管理服务注入
- `trust proxy` 指定具体跳数且上游均为可信网关

## 测试建议（强制）

### 正向测试

- 携带 `Origin: https://evil.example` 与 credentials 发起预检请求，验证 CORS 通配组合放行
- 伪造 `X-Forwarded-For` 验证 `req.ip` 信任面与限流绕过；触发未捕获异常验证明细错误页
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- `NODE_ENV=production` 下验证 helmet 头齐全、错误页无堆栈、诊断面 404
- 白名单外 Origin 请求被 CORS 拒绝；secret 缺失时启动失败（fail-close）

### 回归测试

- 修复后复测中间件顺序未被新路由回退
- 复测环境分支在容器变量错配场景下仍保持生产收紧；新增端点默认继承全局安全中间件

## 证据引用

- `EVID_NODE_CFG_SECURITY_SWITCH`
- `EVID_NODE_CFG_RUNTIME_SETTING`
- `EVID_NODE_CFG_MIDDLEWARE_ORDER`
- `EVID_NODE_CFG_SSR_MODE`
- `EVID_NODE_CFG_ERR_HANDLER`

## 输出

- `node/vuln_audit/config_{timestamp}.md`
- `node/vuln_poc/config_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）

## 机制扩展：安全配置暴露与响应信息披露（2026-09-14 台账轮）

### 机制描述与边界

本扩展覆盖两条暴露链：

- **内部信息披露链**：路由/配置请求 → 文档/配置/元数据响应 → 内部信息暴露。未授权请求者从响应中获得内部实现细节、部署配置、中间件信息。
- **secret 泄露链**：响应字段 → secret material → 凭据泄露。响应中直接携带连接字符串、私钥、access key 等凭据材料。

台账边界（逐字）：发现 secret material 优先归入 secret exposure 路径；公开且预期的 API 文档不判漏洞。

### 重点检查与枚举抓手

每命中记录：文件、行号、端点/响应点、暴露内容类型。

- **配置/元数据端点**：`/debug` / `/config` 等路由导出 `process.env` 或配置对象、`/health`（细节级健康检查暴露依赖信息）、`server-status` / metrics 端点未授权、`swagger` / openapi 文档全量暴露、`.env` / `config.json` 静态文件可下载、生产 source map（`.js.map`）暴露。
- **错误响应披露**：express 错误中间件将 `err.stack` 外泄（如 `app.use((err, req, res, next) => res.status(500).json({ error: err.message, stack: err.stack }))`）、未按环境条件化的详细错误页、错误响应携带内部路径/依赖版本。
- **响应中的 secret 模式**：连接字符串（`mongodb://` / `postgres://` 含口令）、`-----BEGIN PRIVATE KEY-----` / `-----BEGIN RSA PRIVATE KEY-----`、AKIA 形态 access key、JWT 硬编码于响应或前端配置、硬编码 API key。

### 验证矩阵

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **端点访问控制** | 对配置/元数据端点发起未授权请求，确认是否要求认证+授权 | 未授权被拒或仅公开预期文档 → ✅ 安全；未授权可得内部信息 → 🔴 高危待确认 |
| **生产错误页收敛** | 生产配置下触发异常，确认响应为统一错误页，无堆栈/配置/内部路径细节 | 统一收敛 → ✅ 安全；泄露堆栈/配置/内部路径 → 🔴 高危待确认 |
| **secret 模式扫描与响应拦截** | 扫描响应体是否命中连接字符串、私钥头、AKIA、JWT 等 secret 模式，并追踪其进入响应的路径 | 无 secret 入响应 → ✅ 安全；检出可定位来源 → 🔴 高危待确认 |
| **公开文档白名单** | 确认暴露的文档类端点是否属于产品预期公开（如对外公开 API 文档），按预期性排除 | 预期公开 → 不判漏洞；非预期公开 → ⚠️ 待确认 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

### 判定规则

确认需按路径分别闭合 EVID：

**内部信息路径**需同时闭合以下两个 EVID，缺一不可：

1. **端点暴露面闭合**：路由/配置/元数据端点未授权可访问面证据（`EVID_NODE_CFG_SENSITIVE_ENDPOINT_EXPOSURE`）。
2. **内部信息实际披露闭合**：响应实际暴露内部实现/部署配置证据，非仅端点存在（`EVID_NODE_CFG_INTERNAL_INFO_DISCLOSURE`）。

**secret 路径**以第三 ID 替代第二 ID：响应中检出 secret material 的凭据泄露证据（`EVID_NODE_CFG_SECRET_MATERIAL_IN_RESPONSE`）。

🔴 **确认阈值（台账原文）：需证明响应内容实际暴露内部信息或 secret material；仅凭端点存在或字段名疑似不得确认；公开且预期的 API 文档不判漏洞。**

### 测试建议

- **正向**：未授权访问配置/元数据端点，确认获得内部信息；扫描响应确认 secret 模式可检出。
- **负向**：认证+授权收敛、生产错误页统一、secret 入响应被拦截后，不再可利用。
- **回归**：新增元数据/诊断端点（含健康检查、metrics、配置导出）时，复核访问控制与预期公开白名单。

### 证据引用

- `EVID_NODE_CFG_SENSITIVE_ENDPOINT_EXPOSURE`：路由/配置/元数据端点未授权可访问面证据（两路径共用第一 ID）
- `EVID_NODE_CFG_INTERNAL_INFO_DISCLOSURE`：响应实际暴露内部实现/部署配置证据（内部信息路径第二 ID）
- `EVID_NODE_CFG_SECRET_MATERIAL_IN_RESPONSE`：响应中检出 secret material 的凭据泄露证据（secret 路径替代第二 ID）
