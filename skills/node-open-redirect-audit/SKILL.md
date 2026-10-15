---
name: node-open-redirect-audit
description: Node.js 开放重定向审计工具。识别 res.redirect(req.query.url) 与 Next.js redirect 等跳转目标可控及 ///、\、%2F 归一化绕过风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js 开放重定向审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与跳转调用点、returnTo/redirect_uri 参数、目标 allowlist、归一化变体相关的共享抓手
- 若项目存在 RedirectHelper、LoginFlowService、NavigationGuard、CallbackResolver 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐跳转入口、跳转参数与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充登录/登出/回调入口的鉴权边界）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `res.redirect(req.query.url)` / `res.redirect(req.body.returnTo)` 目标直接取请求参数
- Next.js `next/navigation` 的 `redirect()`（Server Actions/Route Handler）与 `pages/api` 的 `res.redirect`
- 登录/登出/OAuth 回调中的 `returnTo`/`next`/`continue`/`redirect_uri`/`callbackUrl` 参数
- 归一化绕过变体：`///evil.com`、`//evil.com`、`\evil.com`、`https:%2F%2F`、`\/\/evil.com`、`javascript:`、`data:`
- allowlist 实现是否 fail-close：白名单外是回退固定页/抛错，还是透传原始值
- `startsWith('/')` 类相对路径校验未排除协议相对（`//`）与反斜杠（`/\`）变体
- `req.headers.host`/`X-Forwarded-Host` 参与拼接待跳转域名的场景
- 支付回跳、邀请链接、深链跳转携带 token/code 等敏感参数外带

## 枚举规则（强制细化）

- 枚举所有跳转调用点：`res.redirect(`、`res.location(`、`res.writeHead(302`、`statusCode = 302`、`redirect(`（next/navigation）、`successRedirect`（passport）
- 优先搜索 `returnTo`、`returnUrl`、`redirect_uri`、`callbackUrl`、`req.query.next`、`req.query.redirect`、`req.query.continue`、`req.query.callback`
- 枚举校验实现：`new URL(`、`startsWith('/')`、`startsWith('http')`、`includes('http')`、allowlist 数组/Map 比对与默认回退分支
- 枚举登录、登出、OAuth 回调、支付回跳、邀请链接、深链跳转、错误回跳等业务场景
- 对每个跳转点记录：目标来源、解码次数、校验逻辑与比对位置、跳转后携带的敏感参数

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 目标 allowlist | 域名白名单数组/Map 比对 | 读取白名单实现源码，确认白名单外是否回退固定页或抛错 | fail-close（回退首页/拒绝）→ ✅ 安全；fail-open（默认放行/透传原始值）→ 🔴 高危 |
| 相对路径校验 | `startsWith('/')` 且排除 `//` 与 `/\` | 验证校验是否在解码后执行、是否覆盖协议相对与反斜杠变体 | 排除全部变体 → ✅ 安全；仅 `startsWith('/')` → ⚠️ 可被 `//evil.com`、`/\evil.com` 绕过 |
| URL 归一化 | `new URL()` 解析后比对 `hostname` | 检查是否先 `decodeURIComponent` 再解析、结构级比对还是字符串级比对 | 解析后比对 → ✅ 安全；字符串级比对 → ⚠️ 可被 `https:%2F%2F` 等编码变体绕过 |
| 协议限制 | 仅允许 http/https | 枚举 `javascript:`/`data:`/`vbscript:` 是否被显式拒绝 | 显式拒绝 → ✅ 安全；未限制 → 🔴 高危 |
| Host 头拼接 | `req.headers.host`/`X-Forwarded-Host` 拼接待跳转域名 | 检查 Host 是否来自可伪造请求头且未校验 | 固定域名常量 → ✅ 安全；直接使用请求头 → ⚠️ 待验证（依赖反代覆盖） |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似直接进入跳转目标位
- `待确认`：上下文显示可疑模式，但目标来源、allowlist 行为或归一化链路不清晰
- `误报`：目标来自固定常量 / 枚举映射，或 allowlist 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到外部可控输入进入跳转目标位的证据 → `确认漏洞`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_REDIRECT_CALL` + `EVID_NODE_REDIRECT_TARGET_CONTROL`：目标直接来自请求参数且无任何校验或校验 fail-open
- allowlist/相对路径校验存在但可被 `//evil.com`、`\evil.com`、编码变体绕过（`EVID_NODE_REDIRECT_ALLOWLIST_VALIDATE` + `EVID_NODE_REDIRECT_ENCODING_BYPASS` 佐证绕过路径可达）
- 跳转链路携带登录票据/授权 code 到外部域，且校验可绕过

### ⚠️待验证

- 目标来源部分可控（如仅 Host 头参与拼接），但反代覆盖与伪造可行性无法确认
- allowlist 存在，但解码次数、`new URL` 解析顺序与比对位置证据不足
- Next.js Route Handler 跳转点存在，但参数来源需补 trace 闭合

### 误报

- 跳转目标来自固定常量 / 路由名（如 `res.redirect('/dashboard')`）
- allowlist fail-close（白名单外一律回退固定页），且归一化在解码后执行（`EVID_NODE_REDIRECT_ALLOWLIST_VALIDATE` + `EVID_NODE_REDIRECT_ENCODING_BYPASS` 双证据闭合）

## 测试建议（强制）

### 正向测试

- 构造 `?next=//evil.com`、`?next=\/\/evil.com`、`?next=https:%2F%2Fevil.com`、`?next=javascript:alert(1)` 验证实际跳转落点
- 验证 OAuth 回调 `redirect_uri` 篡改后 code/token 是否外带
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 白名单外域名与非相对路径被拒绝（fail-close）
- `data:`/`javascript:` 协议被显式拒绝
- 验证白名单外目标回退固定页而非透传原始值

### 回归测试

- 修复后复测归一化变体（双斜杠/反斜杠/编码）仍被拦截
- 新增跳转点接入统一校验函数且保持 fail-close
- 验证白名单变更时未引入通配子域放行

## 证据引用

- `EVID_NODE_REDIRECT_CALL`
- `EVID_NODE_REDIRECT_TARGET_CONTROL`
- `EVID_NODE_REDIRECT_ALLOWLIST_VALIDATE`
- `EVID_NODE_REDIRECT_ENCODING_BYPASS`
- 可选叠加：`EVID_NODE_CFG_SECURITY_SWITCH`（框架/网关层跳转安全开关）

## 输出

- `node/vuln_audit/open_redirect_{timestamp}.md`
- `node/vuln_poc/open_redirect_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
