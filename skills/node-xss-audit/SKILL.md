---
name: node-xss-audit
description: Node.js XSS 审计工具。识别 res.send/res.write 拼接 HTML、dangerouslySetInnerHTML、v-html、SSR 注水等跨站脚本输出风险，输出分级、证据与修复建议。
---

# Node.js XSS 审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 HTML 输出、模板渲染、SSR 注水、DOM 渲染面相关的共享抓手
- 若项目存在 RenderHelper、HtmlBuilder、TemplateEngine 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、序列化配置、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate（服务端输出链）**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- DOM 渲染面（`dangerouslySetInnerHTML` / `v-html` / `innerHTML`）允许以静态证据驱动并显式标注
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `res.send` / `res.write` 直接拼接 HTML 且未编码
- `res.render` 模板中使用未转义输出（EJS `<%-`、Pug `!=`、Handlebars `{{{ }}}`、Nunjucks `autoescape` 关闭）
- React `dangerouslySetInnerHTML` 直接使用外部输入
- Vue `v-html` 直接使用外部输入
- 原生 `innerHTML` 直接赋值外部输入
- SSR 注水上下文（`__NEXT_DATA__` / `__NUXT__`）注入用户可控 JSON 且未做 `>` / `<` / `&` / `"` 等字符转义
- 输出编码缺失或仅在部分分支生效

## 枚举规则（强制细化）

- 枚举所有 `res.send(`、`res.render(`、`dangerouslySetInnerHTML`、`v-html`、`innerHTML`、`__NEXT_DATA__`、`__NUXT__`、`escape-html`、`DOMPurify` 调用点与配置
- 对每个输出点记录：输出 API、Content-Type、是否拼接用户输入、是否经过编码/净化、模板引擎自动转义配置
- 区分服务端输出链（`res.send` / `res.render`）与客户端/同构渲染面（`dangerouslySetInnerHTML` / `v-html` / `innerHTML`）
- 检查模板引擎是否关闭自动转义（如 `nunjucks.configure({ autoescape: false })`）
- 检查模板中是否存在显式原样输出语法（`<%- %>`、`!=`、`{{{ }}}`、`tripleMustache`）
- 检查 `dangerouslySetInnerHTML` / `v-html` / `innerHTML` 的 `__html` / 表达式是否来自外部输入且未先净化
- 检查 SSR 注水脚本中 JSON 序列化是否误用 `serialize-javascript` 的 `unsafe: true` 等关闭转义的选项；若使用 `isJSON` 需确认输入来源可信
- 检查 `escape-html` / `DOMPurify` 是否覆盖所有输出分支且配置严格
- 若存在二次封装，必须逐层展开到真实 HTML 输出或模板渲染点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 模板自动转义 | React / Vue 默认转义；EJS `<%= %>`；Nunjucks 默认 `autoescape`；Handlebars 默认编码 | 检查模板引擎默认转义是否被显式绕过 | 默认转义未被绕过 → ✅ 安全；使用 `<%-` / `!=` / `{{{ }}}` 输出用户数据 → 🔴 高危 |
| 输出净化 | `DOMPurify.sanitize(dirty)` / `escape-html` / `he.encode` | 检查净化函数是否覆盖全部输出分支且配置严格 | 全分支覆盖且配置禁止 `on*` / `style` → ✅ 安全；部分分支未净化 → ⚠️ 待确认；无净化 → 🔴 高危 |
| CSP 头 | `helmet.contentSecurityPolicy` 配置 | 检查响应头是否下发 CSP 并限制 `script-src` / `unsafe-inline` | CSP 限制脚本来源且未放行 `unsafe-inline` → ✅ 纵深防御；无 CSP 或放行 `unsafe-inline` → ⚠️ 纵深防御缺失 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入 HTML 输出或 SSR 注水上下文
- `待确认`：上下文显示可疑模式，但外部输入来源、barrier 行为或调用链不清晰
- `误报`：输入来自固定常量/枚举映射，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到外部可控输入进入 Sink 位的证据 → `确认漏洞`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知/非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_XSS_OUTPUT_POINT` + `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT` + 无有效 Barrier
- `res.send` / `res.write` 直接拼接用户输入并返回 `text/html`
- 模板引擎显式绕过自动转义输出用户输入
- `dangerouslySetInnerHTML` / `v-html` / `innerHTML` 直接放入未净化外部输入
- SSR 注水（`__NEXT_DATA__` / `__NUXT__`）中用户可控 JSON 未做安全转义

### ⚠️待验证

- 上下文显示可疑模式（如 `res.send(template)`），但外部输入来源不清晰（需补 trace 或调用链）
- Barrier 函数（如 `escape-html`、`DOMPurify`）存在，但当前分支是否调用、是否覆盖所有输出路径无法确认
- DOM 渲染面依赖同构数据流，静态无法确认服务端到客户端的传递路径

### 误报

- 输出内容完全静态，无用户可控输入
- 用户输入经 fail-close 编码/净化后进入输出点，且所有分支均覆盖
- 模板引擎默认自动转义未被绕过，用户数据未进入原样输出语法
- SSR 注水使用安全 JSON 序列化库且关闭危险选项

## 测试建议（强制）

### 正向测试

- 构造 `<script>alert(1)</script>`、`<img src=x onerror=alert(1)>`、`javascript:alert(1)` 等 payload
- 验证用户参数进入 `res.send` 拼接、`res.render` 模板原样输出、`dangerouslySetInnerHTML` / `v-html` 后的脚本执行
- 验证 SSR 注水场景中 JSON 闭合标签绕过（`</script><script>alert(1)</script>`）
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造经 `escape-html` / `DOMPurify` 处理后的输入，验证危险标签被转义或剥离
- 验证模板默认转义语法（`<%= %>`、`{{ }}`）对 HTML 元字符正确编码
- 验证 CSP 策略下内联脚本被浏览器拦截

### 回归测试

- 修复后复测，确认编码/净化覆盖所有输出分支
- 复测模板引擎配置，确认未重新开启危险转义绕过
- 验证 SSR 注水序列化库升级后关闭危险选项

## 证据引用

- `EVID_NODE_XSS_OUTPUT_POINT`
- `EVID_NODE_XSS_USER_INPUT_INTO_OUTPUT`
- `EVID_NODE_XSS_ENCODE_OR_SANITIZE`
- `EVID_NODE_XSS_SSR_HYDRATION`

## 输出

- `node/vuln_audit/xss_{timestamp}.md`
- `node/vuln_poc/xss_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
