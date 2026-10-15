---
name: node-spreadsheet-export-audit
description: Node.js 电子表格导出（CSV/Excel）公式注入审计工具。识别 exceljs、csv-stringify、fast-csv、json2csv、手写 CSV 拼接等导出链路中用户可控字段未做公式中和导致的公式/DDE/超链接注入风险，输出分级、证据与修复建议。
---

# Node.js 电子表格导出（CSV/Excel）公式注入审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 的「EXPORT」章作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范（EXPORT 类型码）
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖 EXPORT 章中的导出器定义：`exceljs`（`worksheet.addRow` / `addRows`）、`csv-stringify`（`stringify` / `stringifier.write`）、`fast-csv`、`json2csv`（`new Parser().parse`）、手写 `` `${v1},${v2}` `` CSV 拼接，以及公式注入模式（`=` `+` `-` `@` 开头、DDE 载荷 `=cmd|' /C calc'!A1`、HYPERLINK 钓鱼链）
- 若项目存在统一的 exportService、报表生成器、csv/excel helper 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- **本专项属于 trace-gate 类型**：导出字段的源参数（req.body / req.query / 数据库用户可写列 / 下游存储值）需 `node/route_tracer/{route_id}/trace_{timestamp}.md` 证据闭环；`node/route_tracer/{route_id}/trace_{timestamp}.md` 为硬前置证据，如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐导出端点入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与导出端点短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于确认导出端点匿名可达性、P0/P1 分桶与导出数据的敏感度）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充 Content-Type / Content-Disposition 响应头约定、静态文件中间件与运行时控制面）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致
- trace 缺失或 `trace_status=PARTIAL/UNRESOLVED` 时，所有结论降级为 `⚠️待验证`（见「二阶段判定」）

## 重点检查

- CSV/Excel 导出端点：Express/Koa/Fastify 返回文件下载的 route handler、报表导出、批量数据下载入口
- 导出字段与请求参数 / 数据库用户数据的映射：导出行中哪些列来自用户可控输入（req.body 字段、req.query 参数、数据库中可被用户写入的列）
- 公式前缀中和：写入单元格 / CSV 字段前是否对 `=` `+` `-` `@` 开头的值做 `'` 前缀转义或拒绝
- 单元格格式强制文本：`exceljs` 生成路径是否将用户数据列显式设为文本格式（`cell.numFmt = '@'`），阻止公式解释
- CSV 分隔符与引号转义：`csv-stringify` / `fast-csv` 的配置 vs 手写 `v1 + ',' + v2` 直出（后者常同时缺失引号转义与公式中和）
- 响应呈现一致性：`Content-Type`（`text/csv`、`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`）与 `Content-Disposition`（`attachment; filename=...`）和实际文件扩展名、内容格式是否一致，避免被浏览器/电子表格以错误解释器打开
- 导出内容为纯常量/枚举字典（无用户数据参与）的路径，标记为不相关而非漏洞

## 枚举规则（强制细化）

- 枚举范围限定业务源码；`node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/` 与 coverage 目录不纳入审计面；lockfile（`package-lock.json` / `yarn.lock` / `pnpm-lock.yaml`）属依赖清单而非导出链路，仅用于确认导出器包版本，不单独审计，但不得因 lockfile 命中而跳过业务源码检查
- 枚举所有返回文件下载的导出 route handler，以及 Service / 定时任务 / 队列消费中触发的报表生成与文件落盘路径
- 优先搜索：`exceljs`（`new ExcelJS.Workbook()`、`worksheet.addRow(`、`worksheet.addRows(`、`ws.addRow(`）、`csv-stringify`（`stringify(`、`new Stringifier`、`stringifier.write(`）、`fast-csv`（`csv.write(`、`format({`）、`json2csv`（`new Parser(`、`.parse(`）、手写 CSV 拼接（模板字符串或 `+` 拼接字段后 `res.send(csv)` / `res.end(csv)`）、`Content-Disposition`（`attachment;filename=` 响应头）、`res.download(` / `res.attachment(` 配合 CSV/Excel 内容
- 枚举公式中和辅助函数（如 `sanitizeFormula`、`escapeCell`、`prefixApostrophe`）的定义与全部调用点，确认每条导出链路是否实际调用
- 单独枚举导出字段来源：每列字段来自 req.body / req.query、数据库用户可写列、下游存储值还是固定常量，逐一标注可控性
- 枚举 Excel 单元格格式设置：用户数据列是否显式 `cell.numFmt = '@'`；未设格式的默认 General 格式在多数电子表格中会解释公式
- 对每个命中记录：**文件、行号、包名（exceljs/csv-stringify/fast-csv/json2csv/手写拼接）、字段来源（req.body/req.query/数据库用户数据/常量）、公式中和有无（是/否/不可见）**
- 枚举统一的 exportService、报表生成器、csv/excel helper 的封装链路，追踪到最终单元格/字段写入点

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| **公式前缀中和** | 写入前检测值是否以 `=` `+` `-` `@`（及 Tab/CR 前缀变体）开头，并加 `'` 前缀或拒绝写入（如 `value.replace(/^[=+\-@]/, "'$&")`） | 读取中和函数实现，确认是否为 fail-close（未知前缀一律处理），并确认每条导出链路实际调用 | 全部用户可控字段写入前统一中和且为 fail-close → ✅ 安全；仅部分列中和、中和函数可旁路或实现不可见 → ⚠️ 待确认；完全无中和且字段可控 → 🔴 高危 |
| **单元格格式强制文本** | `exceljs` 路径中用户数据列显式 `cell.numFmt = '@'` 或在列定义中指定文本格式 | 检查 Excel 生成路径中可控列是否显式设置文本格式，而非默认 General | 可控列全部强制文本格式 → ✅ 安全；仅部分列设置或格式设置实现不可见 → ⚠️ 待确认；未设置 → 🔴 高危 |
| **导出字段 allowlist** | 导出的列集合来自固定列清单（常量数组 / 枚举映射），而非由 req.query 动态选择任意可写列 | 读取列选择逻辑，确认列名/列集合是否可被请求参数改变 | fail-close 列清单 → ✅ 安全；列名/列集合来自请求参数且无校验 → 🔴 高危 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入导出生成/单元格写入点
- `待确认`：上下文显示可疑模式，但外部输入来源、barrier 行为或调用链不清晰
- `误报`：输入来自固定常量/枚举映射，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或字段来源，直到满足以下任一条件：

- 找到外部可控输入进入 Sink 位的证据 → `确认漏洞`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**trace-gate 检查**：若 `node/route_tracer/{route_id}/trace_{timestamp}.md` 不存在或 `trace_status=PARTIAL/UNRESOLVED`，所有结论必须降级为 `⚠️待验证`，禁止输出 `✅已确认可利用`。

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知/非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

🔴 **STOP — 仅发现导出生成语法、未证明用户可控字段进入导出内容时，禁止输出「确认漏洞」，结论一律落 `⚠️待验证`，并写明缺失证据与补证动作。**

## 判定规则（强制细化）

### 已确认

必须同时满足以下三项，且三个 EVID 同时引用、缺一不可：

1. **Source 闭合**：导出字段来自用户控制数据（`EVID_NODE_EXPORT_FIELD_USER_CONTROLLED`——req.body / req.query 参数、数据库中用户可写列或下游存储值进入导出数据列的证据）
2. **导出生成 Sink 闭合**：用户可控字段到达导出生成/单元格写入点（`EVID_NODE_EXPORT_FORMULA_SINK`——`exceljs` `addRow`/`addRows` 单元格赋值、`csv-stringify`/`fast-csv`/`json2csv` 字段写入、手写 CSV 拼接写入、`res.send(csv)` 直出的证据）
3. **解释路径与影响闭合**：导出内容会被电子表格解释为公式/命令/链接（`EVID_NODE_EXPORT_INTERPRETATION_PATH`——`.csv`/`.xlsx` 下载后以 Excel/WPS 等电子表格打开、单元格值以 `= + - @` 开头被解释为公式，DDE 载荷或 HYPERLINK 链可被触发的证据）

🔴 **确认阈值（硬性规则）：未同时引用 EVID_NODE_EXPORT_FIELD_USER_CONTROLLED + EVID_NODE_EXPORT_FORMULA_SINK + EVID_NODE_EXPORT_INTERPRETATION_PATH 三者，不得输出「已确认」或 🔴/🟠 级别结论。**

🔴 **普通文本导出（无公式解释可能，如固定模板通知文本、导出内容不含任何可被解释为公式的字符开头且已证明无解释路径）或未证明解释路径时，不得确认。**

### ⚠️待验证

- 仅发现 `addRow` / `stringify` / 单元格写入语法，但未证明写入字段来自用户可控数据（需补 trace 或调用链）
- 导出端点存在，但导出列的字段来源不清晰（需补 trace 确认是否为用户可写数据）
- 公式中和函数存在，但当前导出链路是否调用、是否覆盖全部可控列无法确认
- 异步 / 队列 / 定时报表链路中的导出数据来源未闭合
- 导出内容解释路径不明确（如 `Content-Type` 与扩展名不一致，无法确认以何种解释器打开）
- trace 缺失或 `trace_status=PARTIAL/UNRESOLVED` 时，全部结论降级为此档

### 误报

- 已做公式中和的导出：所有用户可控字段在写入前经 fail-close 中和（`'` 前缀或以 `= + - @` 开头的检测加前缀），且单元格格式强制文本 → 误报
- 导出字段全部来自固定常量/枚举字典，无任何用户可控数据参与
- 导出列锁定于 fail-close 列清单，请求参数不可改变导出列集合
- 导出内容为纯文本格式且客户端无电子表格解释路径（如仅日志导出、仅机器消费的无头 CSV 管线且已证明无人工电子表格打开环节）

### 反例黑名单

| # | 反模式 | 为什么错 | 正确做法 |
|---|---|---|---|
| 1 | 无 trace 时输出 ✅已确认 | 仅凭静态抓手无法证明导出字段的用户可控性 | 降级为 `⚠️待验证`，说明缺失证据 |
| 2 | 发现 `addRow` 即确认高危 | 写入语法 ≠ 字段可控；常量列导出不构成漏洞 | 必须闭合字段来源（EVID_NODE_EXPORT_FIELD_USER_CONTROLLED）后再确认 |
| 3 | `.xlsx` 导出一律判安全 | exceljs 默认 General 格式同样会解释 `=` 开头公式 | 核对单元格格式强制文本与公式中和 |
| 4 | CSV 无公式风险 | Excel 打开 CSV 时 `=cmd|' /C calc'!A1` 同样被解释为 DDE/公式 | 核对 CSV 字段写入前是否做公式中和 |
| 5 | 存在中和函数即判安全 | 中和函数若未被当前导出链路调用、仅覆盖部分列或可旁路则无效 | 核对每条导出链路的实际调用与覆盖范围 |

## 测试建议（强制）

### 正向测试

- 在用户可控字段写入 `=cmd|' /C calc'!A1`（或 `=HYPERLINK("https://evil.example","点击")`），导出后用电子表格打开，验证公式被解释、DDE/超链接链可触发
- 验证 req.body / req.query 参数经 trace 链路进入 `exceljs` `addRow` / `csv-stringify` 写入后，导出文件中的载荷保持原样
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 字段值经公式中和（`'` 前缀）后导出，验证电子表格中显示为字面文本不执行
- 导出列取 allowlist 外列名、含 Tab/CR 前缀变体的值时被 fail-close 拦截
- 验证 `exceljs` 可控列强制文本格式（`numFmt = '@'`）后公式不被解释

### 回归测试

- 修复后复测全部导出链路（含新增导出列时中和逻辑不旁路），确认中和与文本格式 barrier 仍生效
- 复测二次封装的 exportService 与直接调用点，确认未引入新的绕过路径
- 验证导出字段 allowlist 新增列时仍保持 fail-close

## 证据引用

- `EVID_NODE_EXPORT_FIELD_USER_CONTROLLED`
- `EVID_NODE_EXPORT_FORMULA_SINK`
- `EVID_NODE_EXPORT_INTERPRETATION_PATH`

## 输出

- `node/vuln_audit/export_{timestamp}.md`（漏洞编号格式：`{等级前缀}-EXPORT-{序号}`，如 `H-EXPORT-001`，与 `shared/SEVERITY_RATING.md` 类型码 EXPORT 对齐）
- `node/vuln_poc/export_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC，参考 `shared/DOTNET_VULN_POC_TEMPLATE.md`）
- 输出中每个命中必须记录：包名（exceljs/csv-stringify/fast-csv/json2csv/手写拼接）、字段来源（req.body/req.query/数据库用户数据/常量）、公式中和有无、trace_id 与三个 EVID 的引用状态

## 最低验收要求

- 名称、description、职责边界清晰，与 node-cmd-audit 等既有 node 专项不产生大面积重复职责
- 已引用 `shared/NODE_AUDIT_GRABBER_INDEX.md`、`shared/NODE_SINK_REFERENCE.md`、`shared/DOTNET_AUDIT_EXECUTION_STANDARD.md`、`shared/SEVERITY_RATING.md`、`shared/IO_PATH_CONVENTION.md`
- 已具备完整十二章节结构：共享抓手索引引用 + 输入依赖 + 重点检查 + 枚举规则（强制细化）+ Barrier 验证矩阵（强制）+ 二阶段判定（强制）+ 判定规则（强制细化）+ 测试建议（强制）+ 证据引用 + 输出 + 最低验收要求
- 已说明证据引用口径（EVID_NODE_EXPORT_FIELD_USER_CONTROLLED / EVID_NODE_EXPORT_FORMULA_SINK / EVID_NODE_EXPORT_INTERPRETATION_PATH）
- 已说明与 `node/route_tracer`（硬前置）、`node/framework_audit`、`node/auth_audit`、pipeline、cross 端的关系
- 已写明本专项为 trace-gate 类型，`node/route_tracer/*` 属硬前置证据
- Barrier 验证矩阵列头严格为 `| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |`
- 输出路径符合 `shared/IO_PATH_CONVENTION.md`，明确写为 `node/vuln_audit/export_{timestamp}.md` 与 `node/vuln_poc/export_{timestamp}.md`
- 正文含 node 排除规则：`node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`、coverage 目录不纳入审计面；lockfile 例外
