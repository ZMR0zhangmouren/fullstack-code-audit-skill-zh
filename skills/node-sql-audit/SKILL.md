---
name: node-sql-audit
description: Node.js SQL 注入审计工具。识别 mysql/mysql2 query 拼接、knex.raw、sequelize.literal、prisma.$queryRawUnsafe 与 ORDER BY 结构位置风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js SQL 注入审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 SQL 构造、驱动/ORM 调用、参数绑定、Raw 逃生口、结构位置相关的共享抓手
- 若项目存在 DbHelper、QueryService、Repository、SqlBuilder 等二次封装，必须补充到输出中的项目内抓手章节
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

- mysql / mysql2 的 `query(sql)`（整串拼接）与 `execute(sql, params)`（占位符）混用边界
- 模板字符串 `` `SELECT ... WHERE id=${id}` `` 与 `+` 拼接直接进入 `query()` / `pool.query()`
- knex：`knex.raw(拼接串)` 与 `.where({ col: value })` 对象化查询的边界
- sequelize：`sequelize.query(拼接串)`、`sequelize.literal` 与 `replacements` 参数替换的边界
- prisma：`$queryRaw`（tagged template 自动参数化）与 `$queryRawUnsafe` / `$executeRawUnsafe`（整串可控）的区分
- pg / oracledb / mssql 等驱动：`client.query(text, values)` 参数数组化缺失
- ORDER BY 列名、排序方向、表名、IN 列表等无法参数化的结构位置是否有 fail-close 白名单
- LIKE 值的 `%` `_` 通配符注入与自封装转义实现

## 枚举规则（强制细化）

- 用 rg 枚举调用点：`\.query\(`、`\.execute\(`、`\$queryRaw`、`\$queryRawUnsafe`、`\$executeRawUnsafe`、`knex\.raw`、`sequelize\.query`、`sequelize\.literal`
- 枚举模板字符串与拼接 SQL：rg `SELECT `、`INSERT INTO`、`UPDATE `、`DELETE FROM`、`ORDER BY`、`LIMIT `，回溯命中串是否含 `${` 插值或 `+` 拼接
- 对每个调用点记录：驱动/ORM、构造方式（拼接 vs 占位符）、参数来源、是否 Raw 逃生口、连接池与账号权限
- 单独枚举"不可参数化片段"：排序键、列名、表名、分页方向、IN 列表、动态 where 片段，并核对白名单映射实现
- 区分 `$queryRaw`（tagged template 值位参数化）与 `$queryRawUnsafe`（整串直传），禁止混为一谈
- 若存在二次封装（QueryService / SqlBuilder / Repository），必须逐层展开到真实驱动调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 占位符参数化 | mysql2 `execute(sql, [params])` / pg `query(text, values)` | 检查调用点是否以 `?` / `$1` 占位符数组传值，插值是否只落在值位 | 全部值位走占位符 → ✅ 安全；拼接串进入 `query()` → 🔴 高危 |
| ORM Raw 逃生口 | `prisma.$queryRawUnsafe` / `knex.raw` / `sequelize.literal` | 读取调用源码，确认插值变量来源与是否可被外部输入影响 | `$queryRaw` tagged template 或固定 Raw → ✅ 安全；Unsafe 族拼接用户输入 → 🔴 高危 |
| 排序键 / 标识符白名单 | sortKey → 列名映射表 / 枚举 | 读取映射实现，确认只返回固定列名、default 分支 fail-close、排序方向固定 | fail-close 白名单 → ✅ 安全；直接透传列名 / 排序方向 → 🔴 高危 |
| LIKE 值转义 | 自封装 `escapeLike()` | 读取实现源码，确认 `%` `_` `\` 转义与 ESCAPE 子句 | 完整转义 → ✅ 安全；部分转义 → ⚠️ 可绕过；无转义 → 🟠 通配符注入 |
| 输入校验 | joi / zod / 正则 | 检查校验器是否覆盖拼接变量、类型是否强制转换 | fail-close 校验 → ✅ 安全；可截断 / 编码绕过 → ⚠️ 待确认；无校验 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入 SQL 文本拼接或结构位置
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

- `EVID_NODE_SQL_QUERY_POINT` + `EVID_NODE_SQL_STRING_CONCAT` + 无有效 `EVID_NODE_SQL_PARAM_BINDING_GUARD`
- 外部可控参数经模板字符串 / `+` 拼接进入 `query()` / `pool.query()` 整串执行
- `EVID_NODE_SQL_STRUCTURE_POSITION`：ORDER BY 列名、排序方向、表名等结构位置前端可控且无 fail-close 白名单
- Raw 逃生口（`$queryRawUnsafe` / `$executeRawUnsafe` / `knex.raw` / `sequelize.literal`）拼接用户输入且 barrier 为 fail-open

### ⚠️待验证

- 上下文显示可疑拼接（如模板字符串 SQL），但外部输入来源不清晰（需补 trace 或调用链）
- 排序键 / 标识符存在映射逻辑，但当前分支是否调用、返回值是否被使用无法确认
- 异步 / 队列 / 事件链路（如后台报表任务）中的参数传递未闭合

### 误报

- 全部值位走 `execute(?, ...)` / pg `query(text, values)` / `$queryRaw` tagged template / ORM 对象化查询，且结构位有白名单
- 排序键 / 列名来自固定枚举映射，未知输入会拒绝（fail-close）
- 输入仅进入严格转义后的 LIKE 值位，且 SQL 结构完全固定

## 测试建议（强制）

### 正向测试

- 构造确认可利用的注入输入：`' OR 1=1--`、`1; DROP TABLE`、`UNION SELECT`、`' AND (SELECT ...)`
- 验证结构位注入：传入非法 ORDER BY 字段与布尔盲注 payload
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造被 barrier 拦截的输入：白名单外排序字段、非数字 id、含引号字符串
- 验证占位符场景下 `' OR 1=1--` 被当作普通值处理
- 验证 joi / zod / 正则白名单对非法输入明确拒绝

### 回归测试

- 修复后复测，确认占位符与白名单仍然生效
- 复测 Raw 逃生口改造结果，确认未引入新的拼接路径
- 验证排序键新增列时仍保持 fail-close

## 证据引用

- `EVID_NODE_SQL_QUERY_POINT`
- `EVID_NODE_SQL_STRING_CONCAT`
- `EVID_NODE_SQL_PARAM_BINDING_GUARD`
- `EVID_NODE_SQL_STRUCTURE_POSITION`

## 输出

- `node/vuln_audit/sql_{timestamp}.md`
- `node/vuln_poc/sql_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
