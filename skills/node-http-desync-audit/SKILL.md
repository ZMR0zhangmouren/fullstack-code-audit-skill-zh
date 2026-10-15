---
name: node-http-desync-audit
description: Node.js HTTP 请求走私审计工具。识别 Node http_parser（llhttp）与 nginx/Envoy/云 LB 代理链对 Content-Length、Transfer-Encoding 的解析差异与请求走私风险，输出分级、PoC 与修复建议。
---

# Node.js HTTP 请求走私（HTTP Desync）审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 CL/TE 解析、代理链路、header 转发与请求体边界相关的共享抓手
- 若项目存在 http-proxy 封装、ForwardMiddleware、HeaderRewrite 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **静态证据驱动 + 协议实测建议**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- Node `http_parser`（llhttp）对 `Content-Length` 与 `Transfer-Encoding` 的优先级与冲突处理：重复 CL、CL+TE 混用、TE-TE 混淆
- `Transfer-Encoding` 头变体：`Transfer-Encoding: xchunked`、值内空格 / 大小写 / 逗号分隔、重复头、`0\r\n\r\n` 前缀污染
- 反向代理解析差异：nginx / Envoy / HAProxy / 云 LB 与 Node 后端对歧义报文的取舍（优先 TE vs 拒绝双头）
- Node 18+ 对非法 header 的抛错行为版本差异：llhttp 严格模式直接断连 vs 旧版本宽松接受
- Node 前置代理与后端解析器组合：`http-proxy` / `http-proxy-middleware` 对 `rawHeaders` 的透传、去重与重写
- TE 头经代理重写或剥离后与后端 Content-Length 读取组合形成的走私面
- 本专项为协议级漏洞：**需要实测验证，静态分析只能给出候选面**，禁止仅凭关键字命中输出强结论

## 枚举规则（强制细化）

- 枚举所有 `http.createServer`、`https.createServer`、`Content-Length`、`content-length`、`Transfer-Encoding`、`transfer-encoding`、`chunked`、`rawHeaders`、`writeHead`、`setHeader` 出现点
- 枚举代理与转发链：`http-proxy`、`http-proxy-middleware`、`createProxyServer`、`proxy.web(`、`changeOrigin`、`xfwd`
- 枚举运行时解析器配置：`--http-parser`、`maxHttpHeaderSize`、`headersTimeout`、`requestTimeout`、`keepAliveTimeout`、`maxRequestsPerSocket`
- 对每个歧义点记录：CL 值与实际 Body 长度关系、TE 显式值、同一请求中 CL 与 TE 是否共存、代理是否重写或去重该头
- 若仓库内含部署配置（nginx.conf、Envoy yaml、Dockerfile、k8s Ingress），一并列出代理层解析器与版本；缺失时记为环境证据缺口
- 记录 Node 版本（engines / Dockerfile base image）：18+ llhttp 严格拒绝 vs 16 及以下宽松行为

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 解析器一致性 | nginx / Envoy / 云 LB 与 Node llhttp 的 CL/TE 取舍 | 比对前端与后端对重复 CL、CL+TE、TE 变体的解析行为 | 两端一致（均拒绝歧义报文） → ✅ 安全；前端接受后端拒绝（或反之） → 🔴 高危候选 |
| 非法报文拒绝 | Node 18+ llhttp 严格模式 | 构造重复 CL / 非法 TE 报文直连后端，确认是否抛 `HPE_*` 错误并断连 | 抛错断连（fail-close） → ✅ 安全；宽松接受或取第一个值 → 🔴 高危 |
| header 透传控制 | `http-proxy` 对 `rawHeaders` 的透传与重写 | 检查代理是否原样透传、去重或剥离 `Transfer-Encoding` | 原样透传且两端解析一致 → ✅ 安全；去重 / 重写引入歧义 → 🔴 高危候选 |
| 协议链一致 | HTTP/1.1 端到端 vs h2c / 降级链路 | 确认是否存在 HTTP/2 → HTTP/1.1 降级与 h2c 明文升级 | 端到端协议一致 → ✅ 安全；存在降级点 → ⚠️ 需实测确认 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：歧义报文疑似在前端与后端解析差异间形成走私原语
- `待确认`：上下文显示可疑模式，但代理链路、解析器版本或报文构造路径不清晰
- `误报`：报文无歧义边界，或解析链已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到前端与后端解析差异且歧义报文可穿越的证据 → `确认漏洞`（须附实测记录）
- 找到解析链一致拒绝 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对解析器、代理头处理、报文校验必须以失败模式评估。非法 / 歧义报文必须抛错、断连或拒绝，绝不能静默取第一个值或透传；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_DESYNC_FRONTEND_VARIANT` + `EVID_NODE_DESYNC_SMUGGLE_PRIMITIVE` + 实测记录（timeout 差分法或注入 `X` 头探测证实走私成功）
- `EVID_NODE_DESYNC_PROXY_CHAIN` + `EVID_NODE_DESYNC_HEADER_CONTROL`：代理对 TE 去重 / 重写且后端 llhttp 宽松解析，走私请求可达敏感端点并产生副作用

### ⚠️待验证

- 前置代理存在但配置不可见，仅静态命中 CL/TE 歧义点（需补代理证据或实测）
- 歧义报文可构造，但未执行 timeout 差分 / `X` 头探测，端到端走私不可证实

### 误报

- Node 18+ 直接暴露（无前置代理），llhttp 对重复 CL / 非法 TE 抛 `HPE_UNEXPECTED_CONTENT_LENGTH` 等错误并断连（fail-close）
- 代理与后端解析行为一致（均拒绝歧义报文），或无可构造的歧义边界
- 端到端纯 HTTP/2，无降级链路与 h2c 面

## 测试建议（强制）

### 正向测试

- 构造 CL+TE 双头走私报文（前端按 TE 分块、后端按 CL 截断），通过 timeout 差分法确认后端挂起或错位解析
- 注入 `X` 头探测：在走私后缀中携带 `X-Foo: x`，观察下一真实请求是否命中附加头，验证走私成功
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 直连 Node 18+ 后端发送重复 CL / 非法 TE，验证抛错断连
- 验证 nginx 默认配置对 CL+TE 双头的拒绝行为（4xx 响应）
- 验证 `http-proxy` 透传场景下前端与后端行为一致

### 回归测试

- 升级 Node / 代理版本后复测 llhttp 严格性与代理取舍
- 复测新增代理链路（Envoy / 云 LB）后解析差异是否重新出现
- 验证 header 重写逻辑变更后仍保持两端一致

## 证据引用

- `EVID_NODE_DESYNC_FRONTEND_VARIANT`
- `EVID_NODE_DESYNC_SMUGGLE_PRIMITIVE`
- `EVID_NODE_DESYNC_PROXY_CHAIN`
- `EVID_NODE_DESYNC_HEADER_CONTROL`
- 可选叠加：`EVID_NODE_CFG_RUNTIME_SETTING`（Node 版本与 `--http-parser` 等运行时配置证据）、`EVID_NODE_CFG_MIDDLEWARE_ORDER`（前置代理与中间件链顺序证据）

## 输出

- `node/vuln_audit/http-desync_{timestamp}.md`
- `node/vuln_poc/http-desync_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
