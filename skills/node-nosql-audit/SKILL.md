---
name: node-nosql-audit
description: Node.js NoSQL 注入审计工具。识别 req.body/req.query 原样对象直通 mongoose/mongodb 查询与 $where/$regex/$gt 操作符注入风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js NoSQL 注入审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与 MongoDB / mongoose 查询构造、ODM sanitize、操作符注入相关的共享抓手
- 若项目存在 Repository、QueryBuilder、MongoHelper 等二次封装，必须补充到输出中的项目内抓手章节
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

- `req.body` / `req.query` 原样对象直通 `find` / `findOne` / `updateOne`
- `$where` / `$regex` / `$gt` 操作符注入
- mongoose 查询拼接

## 枚举规则（强制细化）

- 枚举所有 `mongoose`、`mongodb`、`.find(`、`.findOne(`、`.updateOne(`、`.aggregate(`、`$where`、`$regex`、`$gt`、`$ne` 调用点
- 对每个查询点记录：驱动 / ODM 包名、查询对象构造方式、参数来源（`req.body` / `req.query` / `req.params` / 解析后字段）
- 区分原样对象直通（`Model.find(req.body)`）与字段级拼接（`Model.find({ field: req.query.x })`）
- 记录操作符使用场景：`$where` 字符串、`$regex` 用户输入、`$gt` / `$ne` / `$in` 等比较操作符
- 记录 ODM sanitize 配置：`express-mongo-sanitize`、`mongoose.set('sanitizeFilter', true)`、`schema.pre('find')` 清洗
- 若存在二次封装，必须逐层展开到真实 mongodb / mongoose 查询调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 类型强制 | `String(req.body.x)` 等显式类型转换 | 检查查询构造前是否将输入强制为基本类型 | 所有查询字段均强转为 string / number 等标量 → ✅ 安全；仍直接传递对象 → 🔴 高危 |
| Schema 对象拒绝 | joi / zod schema 拒绝 object 类型 | 读取 schema 定义，确认是否禁止对象 / 未知键 | fail-close 且禁止对象 → ✅ 安全；仅部分字段校验 → ⚠️ 待确认；无 schema → 🔴 高危 |
| ODM sanitize | `express-mongo-sanitize` / `mongoose.set('sanitizeFilter', true)` | 检查是否启用 sanitize，确认 `$` / `.` 过滤行为 | 启用且不可绕过 → ✅ 安全；配置宽松（如 allowDots） → ⚠️ 待确认；无 → 🔴 高危 |
| 禁用 $where | 不构造 / 不传递 `$where` | 检索源码是否使用 `$where`，包括 `Model.where().$where()` | 未使用 → ✅ 安全；使用且输入可控 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似直接进入查询对象结构或操作符字段
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

- `EVID_NODE_NOSQL_QUERY_POINT` + `EVID_NODE_NOSQL_RAW_OBJECT_PASS` + `EVID_NODE_NOSQL_OPERATOR_INJECTION` + 无有效 Barrier
- `req.body` / `req.query` 原样对象直接传入 `Model.find` / `findOne` / `updateOne` / `aggregate`
- `$where` / `$regex` / `$gt` 等操作符字段来自外部可控输入且无 schema / sanitize 拦截
- mongoose 查询拼接中用户输入进入查询结构

### ⚠️待验证

- 上下文显示可疑查询调用，但外部输入来源不清晰（需补 trace 或调用链）
- Barrier 函数（如 `express-mongo-sanitize`、joi/zod schema）存在，但当前分支是否调用、返回值是否被使用无法确认
- 缺少 `EVID_NODE_NOSQL_TYPE_COERCE_GUARD` 关键证据

### 误报

- 入参类型强制为 string（`String(req.body.x)`），对象无法进入查询结构
- joi / zod schema 明确拒绝 object 类型且 fail-close
- `express-mongo-sanitize` 或 `mongoose.set('sanitizeFilter', true)` 已启用且不可绕过
- 未使用 `$where`，且查询字段均来自固定常量 / 枚举映射

## 测试建议（强制）

### 正向测试

- 构造原样对象直通 payload：`{"username":"admin","password":{"$ne":null}}`
- 构造 `$where` 注入：`{"$where":"this.password.length > 0"}`
- 构造 `$regex` 注入：`{"username":{"$regex":"^admi[n]?"}}`
- 验证未授权数据读取或绕过认证
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造被 barrier 拦截的输入：对象类型被 schema 拒绝、`$` / `.` 被 sanitize 过滤
- 验证类型强制后对象被转换为 `[object Object]` 不再具有操作符语义
- 验证 `$where` 被显式禁用或 schema 禁止该键

### 回归测试

- 修复后复测，确认 schema / sanitize / 类型强制仍然生效
- 复测原样对象直通与操作符注入 payload，确认无法绕过
- 验证新增查询字段时仍经过统一校验

## 证据引用

- `EVID_NODE_NOSQL_QUERY_POINT`
- `EVID_NODE_NOSQL_RAW_OBJECT_PASS`
- `EVID_NODE_NOSQL_OPERATOR_INJECTION`
- `EVID_NODE_NOSQL_TYPE_COERCE_GUARD`

## 输出

- `node/vuln_audit/nosql_{timestamp}.md`
- `node/vuln_poc/nosql_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
