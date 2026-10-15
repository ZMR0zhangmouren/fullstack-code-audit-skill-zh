---
name: node-crlf-audit
description: Node.js CRLF 注入审计工具。识别 res.setHeader/res.append/res.writeHead 与 Set-Cookie 值拼接中的 \r\n 头注入风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js CRLF 审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 Header 写入点、Set-Cookie 值拼接、控制字符过滤、代理透传相关的共享抓手
- 若项目存在 HeaderBuilder、CookieManager、ResponseHelper、DownloadService 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐输出入口、参数来源与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、反代边界、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `res.setHeader(name, value)` / `res.append(name, value)` / `res.writeHead(status, headers)` 值中进入 `\r\n` 的位置
- 版本差异（必须写清）：Node 8 起 `setHeader`/`writeHead` 对含非法字符的 header 值抛错（`ERR_INVALID_CHAR`），14.10+ 另提供 `http.validateHeaderName`/`http.validateHeaderValue` 公开校验 API——经此类 API 的直接命中多为宿主 fail-close，结论强度需按 Node 版本区分
- 仍需覆盖：自建 `http.createServer` 直接 `socket.write` 组包写出、`rawHeaders` 直通、`engines` 声明 <8 的老版本 Node
- 仍需覆盖：`res.append` 拼接路径、对 value 先 decode 再写入的场景
- Set-Cookie 值拼接：`cookie.serialize` 有 fieldContentRegExp 校验，但手工 `name=${user}` 模板串拼接与 Domain/Path 属性拼接无此保护
- Content-Disposition 下载文件名来自请求参数或数据库字段且未过滤 `\r\n`
- 反向代理回源重建响应、内部 HTTP 客户端（axios/got）转发后端头、下游服务注入场景
- 联动面：日志换行注入（winston/pino 模板串）仅记录为关联风险，不单独作为 CRLF 已确认依据

## 枚举规则（强制细化）

- 枚举所有 header 写入点：`res.setHeader(`、`res.append(`、`res.writeHead(`、`res.location(`、`res.set(`、`res.cookie(`、`Set-Cookie`、`Content-Disposition`
- 优先搜索值来源为用户输入的位置：`req.query.`、`req.params.`、`req.body.`、`req.headers.` 进入 header 值的插值
- 枚举过滤实现：`replace(/[\r\n]/g`、`replace(/\r?\n/`、`encodeURIComponent`、自研 stripNewlines/escape 工具
- 枚举自建 http 服务与版本边界：`http.createServer`、`socket.write`、`rawHeaders`、`package.json` 的 `engines.node` 声明
- 对每个输出点记录：header 名、值来源、过滤逻辑与解码次数、Node 版本、是否经反代/内部客户端转发

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 运行时校验 | Node 内置 header 值校验（`ERR_INVALID_CHAR`）、`http.validateHeaderValue` | 确认 Node 版本与写入 API 是否触发内置校验 | Node ≥8 且经 `setHeader`/`writeHead`/`cookie.serialize` → ✅ 宿主拦截（结论降级为环境依赖）；自建 socket 组包/老版本 → 🔴 高危 |
| 输入过滤 | `replace(/[\r\n]/g, '')`、`encodeURIComponent` 工具 | 检查过滤是否覆盖 `\r`、`\n`、`%0d`、`%0a` 及双重解码后的残留 | fail-close 全覆盖 → ✅ 安全；仅过滤 `\n` 不含 `\r` 或仅字面量 → ⚠️ 可绕过 |
| Cookie 序列化 | `cookie.serialize`（fieldContentRegExp 校验） | 检查 Set-Cookie 值是否经 serialize 还是手工模板串拼接 | 经 serialize → ✅ 安全；手工 `name=${value}` 拼接 → 🔴 高危 |
| 代理/转发边界 | nginx/haproxy 与内部 HTTP 客户端对非法响应头的处理 | 区分回源重建、转发与直连场景的逐层行为 | 代理丢弃/报错 → ✅ 安全；透传原始值 → ⚠️ 待验证 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入 header 值且可能携带 `\r\n`
- `待确认`：上下文显示可疑模式，但值来源、过滤行为或运行时拦截不清晰
- `误报`：值来自固定常量 / 枚举映射，或运行时校验已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到外部可控输入携带控制字符进入 header 写出点的证据 → `确认漏洞`
- 找到固定常量映射 / fail-close 过滤或宿主拦截证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_CRLF_HEADER_WRITE_POINT` + `EVID_NODE_CRLF_PAYLOAD_CONTROL`（值含 `\r\n` 且可控），并确认运行时不触发 Node 内置校验（自建组包/老版本/内部转发重建响应）
- Set-Cookie 值手工模板串拼接且过滤为 fail-open（仅过滤 `\n` 不含 `\r`，或未覆盖双重解码）
- `EVID_NODE_CRLF_VALIDATE_STRIP` 证据显示过滤器可被 `%0d%0a` 双重编码绕过且输出点可达

### ⚠️待验证

- 输出点命中，但 Node 版本 / `engines` 声明与运行时校验行为证据不足
- 过滤器存在，但解码次数与 `\r`、`\n` 覆盖范围无法确认
- 反代回源重建场景的逐层行为需环境验证

### 误报

- 输出点无用户输入映射，值来自固定常量
- Node ≥8 且全部 header 写入经 `setHeader`/`writeHead`/`cookie.serialize`，宿主 fail-close 拦截（`EVID_NODE_CRLF_HEADER_WRITE_POINT` + `EVID_NODE_CRLF_VALIDATE_STRIP` 双证据闭合）

## 测试建议（强制）

### 正向测试

- 构造 `?name=a%0d%0aX-Injected: 1` 与双重编码 `%250d%250a` 验证响应头实际注入
- 验证自建 http 服务 / 老版本 Node 下 Set-Cookie 值拼接可拆分响应
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 含 `\r\n` 的值经 `setHeader`/`cookie.serialize` 被 Node 抛错拒绝（fail-close）
- 过滤器对 `\r`、`\n`、`%0d`、`%0a` 及双重解码输入全部拦截
- 验证代理层对非法响应头的丢弃/报错行为

### 回归测试

- 修复后复测，确认过滤器与运行时校验仍生效
- 复测新增 header 写入点统一接入 serialize/过滤工具
- 验证 Node 版本升级后 `validateHeaderValue` 校验路径未被移除

## 证据引用

- `EVID_NODE_CRLF_HEADER_WRITE_POINT`
- `EVID_NODE_CRLF_PAYLOAD_CONTROL`
- `EVID_NODE_CRLF_VALIDATE_STRIP`
- 可选叠加：`EVID_NODE_CFG_RUNTIME_SETTING`（Node 版本/`engines` 运行时边界）、`EVID_NODE_CFG_MIDDLEWARE_ORDER`（过滤中间件挂载顺序）

## 输出

- `node/vuln_audit/crlf_{timestamp}.md`
- `node/vuln_poc/crlf_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
