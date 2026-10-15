---
name: node-dom-xss-audit
description: Node.js DOM-XSS 审计工具。识别客户端代码 innerHTML/document.write/eval 与 location.hash/search、postMessage 等 source 污染流及 dangerouslySetInnerHTML/v-html 风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js DOM-XSS 审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与客户端 DOM sink、浏览器 source、框架危险 API、净化器与 CSP 安全头相关的共享抓手
- 若项目存在 DomRenderer、HtmlBridge、MarkdownRenderer、RichTextEditor 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`（必须覆盖客户端代码目录：`*.js`/`*.jsx`/`*.ts`/`*.tsx`/`*.vue`）
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐页面入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充 SSR 模式、注水数据、安全头等框架控制面）
- 可选：`node/vuln_audit/xss_{timestamp}.md`（服务端 XSS 与 DOM-XSS 存在交叉，可复用部分发现）
- 本专项属于 **静态证据驱动**（客户端代码静态分析为主）：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，发现的客户端入口应尽量回链 `node/cross_analysis/high_risk_routes_{timestamp}.md` 中的 `route_id`

## 重点检查

- 客户端代码（`*.js`/`*.jsx`/`*.ts`/`*.tsx`/`*.vue`）中的 DOM sink：`innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`/`eval`/`new Function`/`location.href` 赋值/`setAttribute`
- 浏览器 source：`location.hash`/`location.search`/`document.referrer`/`window.name`/`postMessage`（`event.data`）/`localStorage`/`sessionStorage`
- `location.href`/`location.replace` 赋值点的协议控制（`javascript:`/`data:`）
- `window.addEventListener('message')` 回调是否校验 `event.origin`
- Next.js `dangerouslySetInnerHTML`（含 props/URL 取值）与 Vue `v-html`、`__html` 直传
- 框架安全 API：`textContent`/`createElement` + `appendChild`/`DOMPurify.sanitize`
- SSR 注水数据（`__NEXT_DATA__`/`__NUXT__`）进入 DOM sink 的链路
- 与服务端 XSS 的边界：服务端渲染输出注入归 node-xss-audit，本专项只覆盖浏览器端执行路径

## 枚举规则（强制细化）

- 在 `*.js`/`*.jsx`/`*.ts`/`*.tsx`/`*.vue` 中枚举 sink：`innerHTML`、`outerHTML`、`insertAdjacentHTML`、`document.write`、`eval(`、`new Function(`、`location.href =`、`location.replace(`、`setAttribute(`、`setTimeout('`
- 枚举 source：`location.hash`、`location.search`、`URLSearchParams`、`document.referrer`、`window.name`、`addEventListener('message'`、`localStorage`、`sessionStorage`
- 优先搜索框架危险 API：`dangerouslySetInnerHTML`、`v-html`、`__html`
- 枚举净化与安全 API：`DOMPurify.sanitize`、`sanitize-html`、`textContent`、`innerText`
- 对每个 sink 记录：source 类型、source→sink 是否同链路直连（URL 参数直接进 sink）、净化器与配置、框架、postMessage origin 校验

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 框架安全 API | `textContent`/`createElement`、React/Vue 默认转义 | 确认 sink 位置是否可用安全 API 替代且实际使用 | `textContent`/默认转义 → ✅ 安全；`dangerouslySetInnerHTML`/`v-html` 且内容含 source → 🔴 高危 |
| 净化器 | `DOMPurify.sanitize`/`sanitize-html` | 检查配置是否允许事件属性、`javascript:` URI、自定义标签 | 默认严格配置 → ✅ 安全；放开 `ADD_TAGS`/`ALLOW_UNKNOWN_PROTOCOLS` → ⚠️ 待确认；无净化 → 🔴 高危 |
| postMessage origin 校验 | `event.origin === 'https://trusted.com'` 白名单 | 检查 `addEventListener('message')` 是否严格比对 `event.origin` | 严格白名单 → ✅ 安全；缺失或 `'*'` → 🔴 高危 |
| URL 协议限制 | `location.href` 赋值前校验协议 | 检查 `javascript:`/`data:` 是否被显式拒绝 | 显式拒绝 → ✅ 安全；未限制 → 🔴 高危 |
| CSP / Trusted Types | CSP `script-src`、`require-trusted-types-for`、helmet 配置 | 检查响应头/meta 与框架安全头配置 | 严格 CSP + Trusted Types → ✅ 缓解；无 CSP 或宽松 → 🟠 需确认 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：浏览器可控 source 疑似进入 DOM sink 或危险框架 API
- `待确认`：上下文显示可疑模式，但 source 来源、净化行为或传递链路不清晰
- `误报`：输入来自固定常量/编译期确定值，或净化器/安全 API 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到可控 source 进入 sink 位的证据 → `确认漏洞`
- 找到固定常量映射 / fail-close 净化证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_DOM_SINK_POINT` + `EVID_NODE_DOM_SOURCE_TRACE`：`location.hash`/`location.search` 等 source 与 sink 同链路可达（如 `elem.innerHTML = location.hash.slice(1)`）
- `EVID_NODE_DOM_URL_PARAM_SINK`：URL 参数直接进 sink 且无净化，或 `postMessage` 回调无 `event.origin` 校验
- `dangerouslySetInnerHTML`/`v-html` 内容来自 URL/props 可控数据且无净化器（`EVID_NODE_DOM_FRAMEWORK_SAFE_API` 证据显示安全 API 未使用）

### ⚠️待验证

- sink 命中但 source 经多层 props/context 传递，中间是否净化不可见
- `DOMPurify.sanitize` 存在但配置项（`ADD_TAGS`/`ALLOW_UNKNOWN_PROTOCOLS`）无法确认
- SSR 注水数据（`__NEXT_DATA__`/`__NUXT__`）到 DOM sink 的链路未闭合

### 误报

- sink 输入为硬编码常量或编译期确定值
- 全链路使用 `textContent`/`DOMPurify` 默认配置（`EVID_NODE_DOM_FRAMEWORK_SAFE_API` + `EVID_NODE_DOM_SOURCE_TRACE` 双证据闭合）
- postMessage 严格 origin 白名单且数据不进入 DOM sink

## 测试建议（强制）

### 正向测试

- 构造 `#<img src=x onerror=alert(1)>` 进入 hash 类 sink、`javascript:alert(1)` 进入 location 赋值点
- 构造跨域 `postMessage` 载荷验证无 origin 校验的回调执行
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 非法 origin 的 postMessage 被拒绝、`javascript:` 协议被拦截
- `DOMPurify.sanitize` 默认配置移除 `<script>` 与事件属性
- 验证 `textContent` 赋值不解析 HTML

### 回归测试

- 修复后复测，确认净化器与 origin 校验仍生效
- 复测框架升级后 `v-html`/`dangerouslySetInnerHTML` 清单未新增未净化用法
- 验证 CSP/Trusted Types 配置变更后仍拦截内联脚本

## 证据引用

- `EVID_NODE_DOM_SINK_POINT`
- `EVID_NODE_DOM_SOURCE_TRACE`
- `EVID_NODE_DOM_FRAMEWORK_SAFE_API`
- `EVID_NODE_DOM_URL_PARAM_SINK`
- 可选叠加：`EVID_NODE_CFG_SECURITY_SWITCH`（CSP/helmet 安全头配置）

## 输出

- `node/vuln_audit/dom_xss_{timestamp}.md`
- `node/vuln_poc/dom_xss_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
