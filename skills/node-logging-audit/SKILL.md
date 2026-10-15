---
name: node-logging-audit
description: Node.js 安全日志审计工具。识别 pino/winston/console 模板串注入、authorization 头与密码等敏感数据入日志、日志篡改面与关键操作审计缺失风险，输出分级、证据和修复建议。
---

# Node.js 安全日志审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与日志写入点、敏感字段、审计事件覆盖、日志留存相关的共享抓手
- 若项目存在 logger 工厂、auditLogger、requestLogMiddleware 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐关键业务入口、审计面与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于关联认证失败、权限拒绝和管理操作等高价值事件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **静态证据驱动**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致
- 职责边界：错误响应泄露堆栈/内部路径归 `node-config-audit`（`EVID_NODE_CFG_ERR_HANDLER`），本专项管日志管道与审计留存

## 重点检查

- pino / winston / console 模板串拼接用户输入 + `\n` 伪造日志条目
- 敏感数据入日志：`authorization` 头、token、密码、手机号/身份证等 PII
- redact / 脱敏配置缺失或字段清单不完整
- 日志文件权限、写入路径可控的篡改面、rotate 与集中收集
- 关键操作（登录、支付、权限变更、导出）审计留存缺失
- 异常堆栈与原始请求体整体写入日志

## 枚举规则（强制细化）

- rg 搜索写入点：`console.log(`、`console.error(`、`logger.info(`、`logger.error(`、`winston.createLogger(`、`pino(`、`log.error(`
- rg 搜索敏感源：`req.headers`、`authorization`、`req.body`、`password`、`token`、`phone`、`idCard`
- rg 搜索防护抓手：`redact`、`censor`、`mask`、`rotate`、`audit`
- 对每个写入点记录：格式串与参数来源、敏感字段、脱敏策略、是否结构化单行、审计事件覆盖
- 核对高价值事件（认证失败、权限拒绝、支付、配置变更）是否有对应日志点与告警联动
- 若日志经二次封装，必须逐层展开到真实 pino / winston / console 写入点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 输入脱敏 | pino `redact` / 脱敏中间件 | 核对 redact 字段清单是否覆盖 authorization、password、token、PII | fail-close 脱敏 → ✅ 安全；无脱敏 → 🔴 高危 |
| 日志注入防护 | 结构化 JSON（pino）/ 换行净化 | 用户输入含 `\n` 写入日志验证是否伪造条目 | 结构化单行或净化 → ✅ 安全；模板串拼接原文 → 🔴 高危 |
| 审计事件覆盖 | 认证/授权/支付/权限变更日志点 | 核对高价值事件是否有日志与告警联动 | 关键操作全覆盖 → ✅ 安全；缺失 → 🔴 高危 |
| 留存与篡改面 | rotate / 文件权限 / 集中收集 | 检查日志文件权限、保留周期与写入口 | 权限收敛且集中收集 → ✅ 安全；本地可写且无防护 → ⚠️ 待确认 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：用户输入或敏感数据疑似进入日志写入点，或关键操作疑似无审计留存
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

- `EVID_NODE_LOG_INJECTION_POINT` + `EVID_NODE_LOG_TAMPER_SURFACE`：用户输入经模板串进日志且换行可伪造条目
- `EVID_NODE_LOG_SENSITIVE_DATA`：`authorization` 头、密码或 PII 明文入日志且无 redact
- `EVID_NODE_LOG_AUDIT_TRAIL`：支付、权限变更等关键操作无任何审计日志留存
- `EVID_NODE_LOG_INJECTION_POINT`：结构化字段（userId、level 等）可被用户输入污染

### ⚠️待验证

- 写入点命中但脱敏逻辑在二次封装中，未展开到 redact 配置
- redact 存在但字段清单覆盖度不明
- 审计事件部分覆盖，但告警与留存链路证据不足

### 误报

- pino redact 完整覆盖敏感字段且日志为结构化 JSON 单行
- 用户输入经编码/净化后入日志，换行被剥离
- 关键操作全部有审计日志并接入告警与集中收集

## 测试建议（强制）

### 正向测试

- 用户名含 `\nINFO ...` 写入日志验证伪造条目；带 `authorization` 请求验证 token 明文落日志
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- redact 下 token 显示 `[Redacted]`；结构化 JSON 单行输出不换行
- 关键操作触发后审计日志与告警均可见

### 回归测试

- 修复后复测新增写入点默认接入脱敏与结构化
- 复测审计事件覆盖清单未随重构遗漏

## 证据引用

- `EVID_NODE_LOG_INJECTION_POINT`
- `EVID_NODE_LOG_SENSITIVE_DATA`
- `EVID_NODE_LOG_TAMPER_SURFACE`
- `EVID_NODE_LOG_AUDIT_TRAIL`

## 输出

- `node/vuln_audit/logging_{timestamp}.md`
- `node/vuln_poc/logging_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）

## 机制扩展：审计完整性篡改与审计可用性淹没（2026-09-14 台账轮）

### 机制描述与边界

本扩展覆盖两条机制链：

- **完整性篡改链**：可控 header/cookie/审计字段入审计记录 → 身份冒用/错误归因。攻击者伪造身份相关字段写入审计内容，导致事后追溯时责任主体被错误归因。
- **可用性淹没链**：高频/大体量写入 → 审计存储耗尽。攻击者通过触发大量审计写入路径，使审计存储先于业务资源耗尽，造成审计证据丢失。

台账边界（逐字）：不把一般业务 DoS 升级为审计可用性问题；不把普通日志缺失归入完整性篡改。

### 重点检查与枚举抓手

每命中记录：文件、行号、写入点/消费路径、字段来源。

**完整性篡改面：**

- **审计写入点**：winston / pino / morgan 审计级别写入、自定义审计中间件（`app.use` 挂载的审计 handler）、显式 `logger.audit/info` 业务审计调用。
- **身份字段来源可信性**：审计记录中的用户标识取自 `req.user` / 会话/认证中间件挂载的认证主体（可信），还是直取 `req.headers['x-user-id']` / 请求体字段 / cookie 中可控值（不可信）。
- **审计字段拼接入记录**：header、cookie、查询串、请求体字段是否未经白名单/转义直接拼接进审计消息，或将整个可控字段对象（含 `req.body` / `req.headers`）JSON 序列化后整体写入审计记录。

**可用性淹没面：**

- **高频写入路径**：循环/批量处理内审计写入（逐条记录循环写审计）、单请求触发多条审计（批量接口每元素一条）且无节流。
- **无节流/采样/配额**：审计写入是否有每请求条数上限、采样策略、写入队列背压；攻击者可控的批量参数（如批量大小上限）是否被审计放大。

### 验证矩阵

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **身份字段可信源校验** | 追踪审计记录中身份字段的赋值来源，确认是否仅取自认证主体（`req.user` / 会话），无直取可控 header/cookie 路径 | 身份字段全部来自认证主体 → ✅ 安全；存在可控源路径 → 🔴 高危待确认 |
| **审计字段消毒/结构化** | 检查可控字段入审计记录前是否经白名单过滤或结构化字段承载（非字符串拼接），转义是否 fail-close | 白名单+结构化承载 → ✅ 安全；原文拼接或消毒缺失 → ⚠️ 待确认 |
| **写入节流与配额** | 确认单请求审计条数上限、采样策略、队列背压是否存在且 fail-close | 有硬上限且超限拒绝/丢弃可控 → ✅ 安全；无上限或超限后静默失败 → 🔴 高危待确认 |
| **存储容量与告警** | 确认审计存储耗尽前是否有容量告警、轮转/归档策略，淹没是否可被运维感知 | 有告警+轮转 → ✅ 安全；耗尽无感知 → ⚠️ 待确认 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

### 判定规则

**完整性篡改确认**需同时闭合以下两个 EVID，缺一不可：

1. **可控字段写入路径闭合**：可控 header/cookie/审计字段实际写入审计记录的写入路径证据（`EVID_NODE_LOG_TAMPERABLE_FIELD_SOURCE`）。
2. **冒用/错误归因影响闭合**：身份冒用/错误归因影响闭合证据（`EVID_NODE_LOG_IDENTITY_MISATTRIBUTION_IMPACT`）。

**可用性淹没确认**需闭合因果链：高频/大体量写入与审计存储耗尽的因果链证据（`EVID_NODE_LOG_FLOODING_EXHAUSTION_PATH`）。

🔴 **确认阈值（台账原文）：一般业务 DoS 不得确认；普通日志缺失不属本扩展。** 完整性篡改需证明可控字段实际写入审计记录并造成冒用/错误归因；可用性淹没需证明高频/大体量写入与审计存储耗尽的因果链。

### 测试建议

- **正向**：伪造 `X-User-Id` 等 header 发起操作，确认审计记录中身份字段被冒用；以高并发/大批量请求触发审计写入，确认存储耗尽或告警。
- **负向**：身份字段仅取认证主体 + 写入节流下，伪造 header 不改变审计归因，高频写入被限流。
- **回归**：新增审计字段或新增批量端点时，复核字段来源可信性与写入配额。

### 证据引用

- `EVID_NODE_LOG_TAMPERABLE_FIELD_SOURCE`：可控 header/cookie/审计字段实际写入审计记录的写入路径证据（完整性闭合第一 ID）
- `EVID_NODE_LOG_IDENTITY_MISATTRIBUTION_IMPACT`：身份冒用/错误归因影响闭合证据（完整性闭合第二 ID）
- `EVID_NODE_LOG_FLOODING_EXHAUSTION_PATH`：高频/大体量写入与审计存储耗尽因果链证据（可用性闭合第三 ID）
