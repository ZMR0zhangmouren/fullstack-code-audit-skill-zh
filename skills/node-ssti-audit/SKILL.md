---
name: node-ssti-audit
description: Node.js 服务端模板注入审计工具。识别 ejs/pug/nunjucks/handlebars 模板串拼接用户输入、模板名可控、引擎选项可控等风险，输出分级、证据与修复建议。
---

# Node.js SSTI 审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与模板引擎入口、模板字符串构造、模板名解析、引擎选项相关的共享抓手
- 若项目存在 TemplateService、ViewRenderer、MailTemplate 等二次封装，必须补充到输出中的项目内抓手章节
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

- ejs / pug / nunjucks / handlebars / mustache 模板字符串直接拼接用户输入（非表达式参数化）
- `res.render` 模板名来自用户可控输入
- 模板引擎 `.compile(` 直接消费用户输入字符串
- 模板引擎选项可控（如 ejs 的 `delimiter`、`context` 等）
- 模板与数据未分离，用户输入被解释为模板表达式

## 枚举规则（强制细化）

- 枚举所有 `ejs`、`pug`、`nunjucks`、`handlebars`、`mustache`、`.compile(`、`.render(`、`res.render(` 调用点
- 对每个模板调用点记录：模板来源（文件/字符串）、模板名来源、数据对象来源、引擎选项、是否启用沙箱
- 区分模板文件渲染（`res.render(view, data)`）与模板字符串渲染（`ejs.render(str, data)` / `nunjucks.renderString(str, context)` / `handlebars.compile(str)(data)`）
- 检查模板字符串是否由用户输入拼接或完全来自用户输入
- 检查 `res.render` 第一个参数（模板名）是否来自 `req.query` / `req.params` / `req.body`
- 检查模板引擎选项是否来自外部输入（如 ejs 的 `delimiter`、`compileDebug`，handlebars 的 `strict`）
- 检查是否禁用沙箱/严格模式导致可访问 `require`、`process`、`child_process` 等全局对象
- 识别 lodash.template、doT、eta 等其他模板引擎的同类风险
- 若存在二次封装，必须逐层展开到真实模板引擎调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 模板与数据分离 | `render(name, data)` 参数化；模板名字面量或来自受控映射 | 检查模板名/模板字符串是否固定，用户输入仅进入 data | 模板名固定 / 白名单且 data 参数化 → ✅ 安全；模板串来自用户输入 → 🔴 高危 |
| 模板名 allowlist | 模板名字典映射 / 路径前缀白名单 | 读取模板选择逻辑，确认未知模板名拒绝执行 | fail-close（枚举外拒绝 / 抛异常） → ✅ 安全；fail-open（默认拼接路径） → ⚠️ 可绕过；无校验 → 🔴 高危 |
| 禁用用户可控引擎选项 | ejs `delimiter` 固定；handlebars helper 受控注册；不暴露 `compileDebug` 等选项 | 检查引擎 options 对象是否来自外部输入 | 选项来自固定常量 → ✅ 安全；选项来自 `req.query` / `req.body` → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入模板字符串、模板名或引擎选项
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

- `EVID_NODE_SSTI_RENDER_POINT` + `EVID_NODE_SSTI_TEMPLATE_CONCAT` + 无有效 Barrier
- 用户输入直接拼接到模板字符串并被模板引擎编译/渲染
- `res.render` 模板名来自用户可控输入且无 allowlist
- 模板引擎选项（如 ejs `delimiter`）来自用户输入并可改变模板解析语义

### ⚠️待验证

- 上下文显示可疑模式（如 `ejs.render` 调用），但外部输入来源不清晰（需补 trace 或调用链）
- Barrier 函数（如模板名白名单）存在，但当前分支是否调用、返回值是否被使用无法确认
- 模板字符串部分来自外部输入，但当前调用点无法确认是否进入模板表达式上下文

### 误报

- 模板名为固定字面量，用户输入仅进入 `data` 对象且模板自动转义未被绕过
- 模板字符串完全静态，无用户可控拼接
- 模板名 allowlist 为 fail-close，未知模板名拒绝执行
- 模板引擎选项来自固定常量，用户输入不可达

## 测试建议（强制）

### 正向测试

- 构造 SSTI payload：`<%= process.mainModule.require('child_process').execSync('id').toString() %>`（ejs）、`#{process.mainModule.require('child_process').execSync('id')}`（pug）、`{{ process.mainModule.require('child_process').execSync('id') }}`（nunjucks）等；注意引擎差异：Handlebars / Mustache 默认不会执行任意 JS，通常需借助自定义 helper 或沙箱绕过才能触发 SSTI
- 验证用户参数进入模板字符串后被作为表达式执行
- 验证模板名可控导致读取任意模板文件或执行路径穿越
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造模板字符串参数化输入：用户数据仅作为普通变量输出
- 验证模板名白名单对未知模板名明确拒绝
- 验证引擎选项固定常量时，外部输入无法改变解析行为

### 回归测试

- 修复后复测，确认模板字符串不再拼接用户输入
- 复测模板名 allowlist 与引擎选项固定策略
- 验证新增模板或选项时仍保持 fail-close

## 证据引用

- `EVID_NODE_SSTI_RENDER_POINT`
- `EVID_NODE_SSTI_TEMPLATE_CONCAT`
- `EVID_NODE_SSTI_TEMPLATE_NAME_CONTROL`

## 输出

- `node/vuln_audit/ssti_{timestamp}.md`
- `node/vuln_poc/ssti_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
