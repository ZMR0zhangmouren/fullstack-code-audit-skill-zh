---
name: node-ssrf-audit
description: Node.js SSRF 审计工具。识别服务端 axios/fetch/got/request/undici URL 可控与重定向绕过风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js SSRF 审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与服务端 HTTP 客户端调用、URL 拼接、重定向配置相关的共享抓手
- 若项目存在 HttpClient、WebHookClient、RequestHelper 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、序列化配置、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- 服务端 `axios` / `fetch` / `got` / `request` / `undici` URL 可控
- 重定向跟随绕过 allowlist
- 协议（`file:` / `gopher:`）与内网段校验缺失

## 枚举规则（强制细化）

- 枚举所有 `axios.`、`fetch(`、`got(`、`request(`、`undici`、`http.get`、`https.get`、`followRedirects`、`maxRedirects` 调用点
- 对每个调用点记录：HTTP 客户端包名、URL 构造方式（拼接 / 模板字符串 / `baseURL` + `url`）、参数来源
- 记录重定向相关配置：`followRedirects`、`maxRedirects`、`beforeRedirect` 回调、协议限制
- 记录 URL 校验逻辑：协议白名单、主机白名单、DNS 解析后 IP 校验、内网段拦截
- 识别特殊协议风险：`file://`、`gopher://`、`dict://`、`ftp://` 是否被显式禁止
- 若存在二次封装，必须逐层展开到真实 HTTP 客户端调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| URL allowlist | 协议 + 主机 + 端口白名单 | 读取 allowlist 实现，检查协议限制（仅 http/https）、主机匹配方式、端口范围 | fail-close 且禁止 `file` / `gopher` 等危险协议 → ✅ 安全；允许通配或反射 origin → ⚠️ 待确认；无 allowlist → 🔴 高危 |
| DNS 解析后 IP 校验 | 解析 URL 主机后检查 IP 是否属于内网 / 保留段 | 检查代码是否先 `dns.lookup` 再校验，防止 DNS rebinding | 解析后校验且覆盖 IPv4 / IPv6 / 短格式 / CIDR → ✅ 安全；仅字符串正则匹配主机名 → ⚠️ 待确认；无校验 → 🔴 高危 |
| 重定向控制 | `followRedirects` / `maxRedirects` | 检查 HTTP 客户端配置，是否禁止跟随重定向或逐跳重新校验 | 禁止跟随或逐跳重新执行 allowlist/DNS 校验 → ✅ 安全；允许自动跟随且未逐跳校验 → 🔴 高危 |
| 响应限制 | 响应大小 / 超时限制 | 检查是否配置 `timeout` / `maxBodyLength` / `responseType` / 最大读取字节 | 有限制且 fail-close（超限时抛异常 / 截断） → ✅ 安全；无限制 → ⚠️ 待确认 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入 HTTP 客户端 URL 参数或重定向目标
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

- `EVID_NODE_SSRF_HTTP_CALL_POINT` + `EVID_NODE_SSRF_URL_CONSTRUCTION` + 无有效 Barrier
- 外部可控参数直接进入 URL 字符串或 `baseURL` / `url` 拼接位置，且无 allowlist / DNS 校验
- allowlist 存在但可被重定向跟随绕过（如未逐跳校验、允许 302 到内网）
- 未禁用 `file:` / `gopher:` 等危险协议，且用户可控制协议部分

### ⚠️待验证

- 上下文显示可疑 HTTP 调用，但外部输入来源不清晰（需补 trace 或调用链）
- allowlist / DNS 校验存在，但当前分支是否调用、返回值是否被使用无法确认
- 缺少 `EVID_NODE_SSRF_REDIRECT_FOLLOW` 或 `EVID_NODE_SSRF_ALLOWLIST` 关键证据

### 误报

- URL 完全静态或 allowlist 不可绕过（fail-close）
- DNS 解析后 IP 校验覆盖内网 / 保留段，且重定向被禁止或逐跳校验
- 危险协议被显式禁用，未知协议直接拒绝

## 测试建议（强制）

### 正向测试

- 构造内网目标 URL：`http://127.0.0.1:22/`、`http://169.254.169.254/latest/meta-data/`、`http://[::1]/`
- 构造危险协议 payload：`file:///etc/passwd`、`gopher://127.0.0.1:6379/_INFO`
- 构造重定向绕过：白名单外域名 302 跳转到内网，验证是否被逐跳拦截
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造被 barrier 拦截的输入：协议非 http/https、主机不在白名单、DNS 解析后命中内网段
- 验证 allowlist 对大小写 / 编码 / 端口变形的处理
- 验证 `followRedirects:false` 或 `maxRedirects:0` 时重定向不被自动跟随

### 回归测试

- 修复后复测，确认 allowlist / DNS 校验 / 重定向控制仍然生效
- 复测协议白名单与内网段拦截，确认未引入新的绕过路径
- 验证新增白名单主机时仍保持 fail-close

## 证据引用

- `EVID_NODE_SSRF_HTTP_CALL_POINT`
- `EVID_NODE_SSRF_URL_CONSTRUCTION`
- `EVID_NODE_SSRF_ALLOWLIST`
- `EVID_NODE_SSRF_REDIRECT_FOLLOW`

## 输出

- `node/vuln_audit/ssrf_{timestamp}.md`
- `node/vuln_poc/ssrf_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
