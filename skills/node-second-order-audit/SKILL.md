---
name: node-second-order-audit
description: Node.js 二次注入审计工具。识别用户输入经 Mongoose/Redis/文件存储后在管理后台渲染、邮件模板、CSV 导出、SQL 再拼接等二阶触发点的注入风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js 二次注入（Second-Order）审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与存储入口（DB/缓存/文件/会话写入）、触发入口（渲染/导出/SQL 拼接/命令执行）相关的共享抓手
- 若项目存在 Repository、CacheService、MailService、ExportService 等数据访问与业务封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 必需：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐存储入口和触发入口的 `route_id`）
- 必需：`node/route_tracer/*_{timestamp}.md`（用于追踪存储到触发的完整数据流）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充存储入口与触发入口的鉴权状态差异）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充队列/后台任务/会话配置）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate（跨入口）**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；必须同时分析多个 route_id 的存储-触发配对，消费各配对 route 的 trace 产物；如存在 `trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- 一阶存储：注册名/昵称/收货地址/上传文件名等用户可控数据入库（mongoose `save`/`insertOne`、knex/sequelize `insert`、`redis.set`、`fs.writeFile`）
- 二阶触发-管理后台渲染：存储值经 `res.render`（ejs `<%- %>`/pug `!{}`）原样输出
- 二阶触发-邮件模板：存储值进入 nodemailer 模板或文本上下文
- 二阶触发-CSV/Excel 导出：`json2csv`/`exceljs` 中存储值进入单元格的公式注入（`=HYPERLINK`/`=CMD`）
- 二阶触发-SQL 取出再拼接：`knex.raw`/`$queryRawUnsafe`/`sequelize.literal` 中存储值被二次拼入查询
- 二阶触发-后台任务：BullMQ/Agenda 消费存储路径/参数执行 child_process 或文件操作
- 存储与使用两阶段编码不一致：写入时编码而取出时原样输出（或相反、或输出上下文错位）
- 信任边界差异：存储入口普通用户可写，触发入口为管理员后台或匿名可触达的导出/渲染

## 枚举规则（强制细化）

- 枚举存储入口：`.save(`、`insertOne(`、`insertMany(`、`bulkWrite(`、`.create(`、`redis.set(`、`fs.writeFile(`、`req.session.` 赋值
- 枚举触发入口：`.find(`、`findOne(`、`redis.get(`、`fs.readFile(`、`res.render(`、`<%-`、`!{`、`json2csv`、`exceljs`、`nodemailer`、`knex.raw(`、`$queryRawUnsafe`、`sequelize.literal(`
- 按存储键配对：集合名/表名、缓存键模式、文件路径模式、消息队列 Topic/Channel 对齐存储与触发两侧
- 对每个配对记录：存储入口 route_id、写入来源与可控性、触发入口 route_id、触发条件与触发者身份、两阶段编码方式
- 记录信任边界差异（存储入口鉴权状态 vs 触发入口鉴权状态）与租户/用户隔离条件
- 若存在 Repository/CacheService/MailService 等封装，必须逐层展开到真实存储与触发调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 写入前净化 | sanitize-html/xss 包/escape-html 在写入口处理 | 检查写入口是否净化且 fail-close（非法输入拒绝而非透传） | fail-close 净化 → 存储层可能不成立；无净化或 fail-open → 🔴 高危 |
| 读取后编码一致性 | ejs `<%= %>` 自动转义 vs `<%- %>`、React 默认转义 vs dangerouslySetInnerHTML | 对比存储与使用两阶段编码方式是否与输出上下文匹配 | 两阶段一致且正确 → ✅ 安全；不一致（`EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH`）→ 🔴 高危 |
| 参数化 | 取出值仍走占位符/参数绑定 | 检查二次查询是否经 `knex.raw`/`$queryRawUnsafe` 字符串再拼接 | 参数绑定 → ✅ 安全；字符串再拼接 → 🔴 高危 |
| 信任边界差异 | 存储入口普通用户可写 vs 触发入口管理员后台/匿名导出 | 对比两侧鉴权要求与触发者身份 | 存在差异且触发侧低权限 → 🔴 高危放大；权限相同 → 风险降级 |
| 隔离与后台权限 | 租户/用户数据隔离、BullMQ Worker 执行账户 | 检查攻击者数据是否可被目标用户/高权限 Worker 触发 | 严格隔离 → 风险降级；无隔离/高权限 Worker → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每个存储-触发配对先给出三选一临时结论：

- `确认漏洞候选`：可控输入入库且疑似存在未防护的二阶触发上下文
- `待确认`：存储或触发单侧命中，但配对关系、数据流或编码一致性不清晰
- `误报`：取出后走参数绑定/自动转义，或触发上下文无注入位

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到存储值进入触发上下文且无有效 barrier 的证据 → `确认漏洞`
- 找到参数绑定/两阶段编码一致的 fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_SECOND_ORDER_STORE_POINT` + `EVID_NODE_SECOND_ORDER_TRIGGER_CONTEXT` + `EVID_NODE_SECOND_ORDER_STORAGE_TYPE` 三点闭合：可控输入入库且取出后进入渲染/导出/SQL/命令上下文
- `EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH`：写入与触发两阶段编码不一致（如写入时 HTML 编码、导出为 CSV 公式位原样输出；或 `<%- %>`/`!{}` 原样渲染存储值）
- 触发入口与存储入口存在信任边界差异，且触发侧可低权限/匿名触达

### ⚠️待验证

- 存储或触发单侧命中，配对与数据流映射缺一跳
- 队列消费链（BullMQ/Agenda）触发条件、Worker 执行权限无法确认
- 两阶段编码方式证据不完整，无法确认输出上下文

### 误报

- 取出后全部走参数绑定或模板自动转义，两阶段编码一致（`EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH` 排除）
- 存储值仅回到写入者本人会话且无权限差异、无跨用户触达面
- 触发上下文为纯数值/布尔比较，无语法注入位

## 测试建议（强制）

### 正向测试

- 步骤1：注册名/收货地址写入 `<svg onload=alert(1)>`；步骤2：管理员后台列表页/导出触发执行
- 写入恶意列名触发报表查询；写入 `=HYPERLINK("http://evil.com")` 触发 CSV/Excel 导出
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 写入前净化拒绝恶意输入；取出后参数化/模板自动转义使注入失效
- 触发入口鉴权/租户隔离下攻击者数据不可被目标用户触达
- 验证导出层对 `=`、`+`、`-`、`@` 开头单元格的转义

### 回归测试

- 修复后复测存储与触发双点，确认编码一致性保持
- 复测队列消费链未引入新的高权限执行路径
- 新增导出/渲染/后台任务点纳入两阶段编码核查

## 证据引用

- `EVID_NODE_SECOND_ORDER_STORE_POINT`
- `EVID_NODE_SECOND_ORDER_TRIGGER_CONTEXT`
- `EVID_NODE_SECOND_ORDER_STORAGE_TYPE`
- `EVID_NODE_SECOND_ORDER_ENCODE_MISMATCH`
- 可选叠加：`EVID_NODE_CFG_MIDDLEWARE_ORDER`（净化/鉴权中间件挂载顺序）

## 输出

- `node/vuln_audit/second_order_{timestamp}.md`
- `node/vuln_poc/second_order_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
