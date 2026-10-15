---
name: node-logic-audit
description: Node.js 业务逻辑审计工具。识别 check-then-act 竞态、金额/数量客户端可改、优惠券重复使用、多步流程跳步与 BullMQ 队列重复消费风险，输出分级、证据和修复建议。
---

# Node.js 业务逻辑审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与业务状态迁移、并发控制、幂等保护、金额数量复核相关的共享抓手
- 若项目存在 orderService、paymentService、promotionService、queueConsumer 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐业务动作入口、批量接口与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于确认金额/数量字段的客户端来源与上下游联动）
- 可选：`node/design_intent/design_intent_{timestamp}.md`（意图层参考：业务规则、状态机与权限意图的判定基准，仅用于生成假设与缩小枚举范围，禁止作为 EVID 引用源，见 `shared/AUDIT_EXECUTION_COMMON.md` §9）
- 可选：`node/route_mapping/feature_api_map_{timestamp}.md`（功能视图：按功能面组织逻辑判定基准，视图层参考禁止作 EVID 引用源，见 `shared/AUDIT_EXECUTION_COMMON.md` §9）
- 本专项属于 **静态证据驱动**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致
- 职责边界：接口级身份与资源归属鉴权归 `node-auth-audit`，本专项管鉴权之外的业务约束面（竞态、幂等、状态机、限额复核）

## 重点检查

- check-then-act 竞态：查余额→扣款、库存校验→下单，两步非原子
- 金额/数量客户端可改且服务端未复核（price、quantity、total 直信请求体）
- 优惠券/邀请码重复使用：核销无幂等键、无唯一索引、无状态机前置条件
- 多步流程跳步：`state` / `step` 参数前端控制，服务端不校验前置状态
- BullMQ / node-cron / setInterval 定时任务重复消费与幂等缺失（at-least-once 重复投递）
- 重复提交（double submit）导致重复扣款、重复发放
- 批量操作缺少逐条数量与业务校验（权限逐条校验归 `node-auth-audit`）

## 枚举规则（强制细化）

- 若 `node/design_intent/` 产物存在，优先核对其「业务规则清单 / 状态机与流程约束」逐条在代码中的实现与偏差（偏差登记为文档-实现漂移，不直接升级为漏洞结论）
- 枚举状态变更路由与业务动作：rg 搜索 `router.post(`、`pay`、`refund`、`confirm`、`cancel`、`redeem`、`coupon`、`invite`、`withdraw`、`approve`
- rg 搜索并发与幂等抓手：`findOneAndUpdate(`、`$inc`、`startSession(`、`transaction(`、`redlock`、`SET NX`、`idempotency`、`version`
- rg 搜索队列与定时任务：`BullMQ`、`new Worker(`、`queue.add(`、`node-cron`、`setInterval(`
- 对每个业务动作记录：前置校验→状态更新→副作用 三段是否原子、幂等键、并发控制、金额/数量数据源
- 区分服务端重算与客户端直通：核对 `req.body` 中的 price/quantity/total 是否被服务端数据源覆盖
- 若业务动作经二次封装或消息队列，必须逐层展开到真实 DB 写入点
- **按功能面组织判定（2026-09-19）**：对 coverage 内每个含写操作/资金/租户边界的 P0/P1 功能，列业务约束断言（源自 design_intent 规则 + 功能名语义），到该功能端点逐一在 trace 层验证；功能面无断言的端点按既有代码证据路径兜底，**不得因功能视图缺失跳过**

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 原子化更新 | `findOneAndUpdate` 条件更新 / DB 事务 / 乐观锁 version | 核对校验与写入是否原子（条件更新/事务/锁） | 条件原子更新或事务包裹 → ✅ 安全；先查后写分离 → 🔴 高危 |
| 幂等控制 | 幂等键 / 唯一索引 / 状态机前置条件 | 同一请求重复提交验证结果 | 唯一约束或状态机拒绝 → ✅ 安全；无幂等 → 🔴 高危 |
| 服务端复核 | 金额/数量以服务端数据源重算 | 篡改 price/quantity/total 重放请求 | 服务端重算覆盖 → ✅ 安全；直信客户端字段 → 🔴 高危 |
| 流程状态机 | `state`/`step` 由服务端会话或 DB 持有 | 跳步直接调用后续接口 | 服务端校验前置状态 → ✅ 安全；step 参数直通 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：校验与敏感动作疑似非原子，或流程状态、限额可被客户端操控
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

- `EVID_NODE_LOGIC_RACE_WINDOW` + `EVID_NODE_LOGIC_LIMIT_CONTROL`：查余额→扣款两步非原子且金额未服务端复核
- `EVID_NODE_LOGIC_TOCTOU_PAIR`：库存校验点与下单使用点分离，无事务/锁/条件更新
- `EVID_NODE_LOGIC_WORKFLOW_BYPASS`：`state`/`step` 前端直通且服务端不校验前置状态
- `EVID_NODE_LOGIC_LIMIT_CONTROL`：优惠券核销无幂等键与唯一索引，可重复使用

### ⚠️待验证

- 竞态窗口存在，但 redis 锁/事务的实现与覆盖范围不明确
- 队列消费有重试配置，但幂等与去重证据不足
- 金额字段来源需补 `cross/api_contract_map_{timestamp}.md` 或调用链

### 误报

- 更新走条件原子操作（`$inc` + 条件/唯一索引），重复请求被幂等键拒绝
- 金额/数量全部服务端重算，客户端字段仅作展示
- 流程状态由服务端持有，跳步请求被状态机拒绝

## 测试建议（强制）

### 正向测试

- 并发 N 次重复扣款/下单请求验证超扣、超发；篡改 `price=0.01` 验证成交价
- 重放优惠券核销请求验证重复使用；跳步调用验证流程绕过
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 事务/唯一索引下重复提交被拒绝；篡改金额被服务端重算覆盖
- 跳步请求被状态机拦截并返回明确错误

### 回归测试

- 修复后复测竞态窗口与幂等未回退
- 新增队列消费者与定时任务默认接入幂等键

## 证据引用

- `EVID_NODE_LOGIC_RACE_WINDOW`
- `EVID_NODE_LOGIC_TOCTOU_PAIR`
- `EVID_NODE_LOGIC_WORKFLOW_BYPASS`
- `EVID_NODE_LOGIC_LIMIT_CONTROL`

## 输出

- `node/vuln_audit/logic_{timestamp}.md`
- `node/vuln_poc/logic_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）

## 机制扩展：整数溢出（2026-09-14 台账轮）

### 机制描述与边界

用户数值 → 数值算术 → 溢出/精度丢失致逻辑失败/可用性损失。攻击者提交边界外数值（极大值、负值），使 JS `Number`（IEEE 754 双精度，超过 `Number.MAX_SAFE_INTEGER`（2^53）后整数精度丢失）、位运算截断（`| 0` 回绕为 32 位）、定宽 Buffer 长度/偏移计算等路径产生错误结果，导致价格计算错误、长度/偏移异常、权限判断绕过或拒绝服务。

台账边界（逐字）：纳入既有数值校验维度，不新建算术 Skill。

### 重点检查与枚举抓手

每命中记录：文件、行号、算术点、涉及数值语义与边界来源。

- **用户可控数值入算术**：`parseInt(req.query.n)`（注意非十进制 radix 参数误用）/ `Number(req.body.x)` 解析请求参数后参与加减乘；模型字段直接得到的数值进入运算。
- **2^53 精度丢失上下文**：金额/计数/ID 累加超过 `Number.MAX_SAFE_INTEGER` 后静默精度丢失，缺少 `BigInt` 的场景（大整数 ID、雪花 ID 算术、分↔元换算累计）。
- **长度/偏移计算**：Buffer 操作（`buf.slice(offset, offset + len)`、`buf.readUInt32BE(offset)`）的可控参数参与算术后再作长度/偏移；`new Array(len)` / `Buffer.alloc(len)` 分配大小由可控算术结果决定，乘法溢出/精度丢失致分配过小或异常。
- **位运算截断**：`| 0`、`>>> 0`、`& 0xffffffff` 等将数值截断回绕为 32 位，大数经位运算后回绕改变语义。
- **货币/积分换算**：分↔元乘除（`amount * 100` / `cents / 100`）、汇率乘除，中间结果超安全整数范围。
- **自增/累计器**：计数器、序号生成器无上限保护，达到 2^53 后精度丢失或异常。

### 验证矩阵

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **边界检查前置** | 确认算术运算前是否做 min/max 边界校验（如 `amount > 0 && amount <= LIMIT`），校验是否 fail-close | 前置校验 fail-close → ✅ 安全；无校验或校验后可绕 → 🔴 高危待确认 |
| **安全整数范围强制** | 确认关键算术点是否使用 `BigInt`/字符串大数运算，或经 `Number.isSafeInteger` 前置校验 | 关键算术不依赖 2^53 内精度 → ✅ 安全；关键算术超 2^53 且无防护 → 🔴 高危待确认 |
| **位运算语义匹配** | 确认 `| 0` / `>>>` 等截断运算的输入域是否被校验在 32 位内，大数是否被截断回绕 | 输入域受限 → ✅ 安全；大数截断改变语义 → ⚠️ 待确认 |
| **回绕防护** | 确认累计器/计数器达上限时的处理（拒绝、重置、告警），非静默精度丢失 | 安全处理 → ✅ 安全；静默丢失 → ⚠️ 待确认 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

### 判定规则

确认需同时闭合以下三个 EVID，缺一不可：

1. **用户源闭合**：用户可控数值进入算术运算的源定位证据（`EVID_NODE_LOGIC_NUMERIC_USER_SOURCE`）。
2. **算术点闭合**：加减乘/长度偏移/货币积分换算等算术运算点证据（`EVID_NODE_LOGIC_ARITHMETIC_POINT`）。
3. **影响闭合**：溢出/精度丢失或边界绕过导致逻辑失败/可用性损失的影响证据（`EVID_NODE_LOGIC_OVERFLOW_IMPACT`）。

🔴 **确认阈值（台账原文）：需证明溢出/精度丢失/边界绕过造成逻辑失败，非仅存在数值转换。**

已安全整数校验（`Number.isSafeInteger`）+ 前置边界校验为误报。

### 测试建议

- **正向**：以超 `Number.MAX_SAFE_INTEGER` 金额、负长度、超大分页参数、非十进制字符串触发边界输入，确认精度丢失/回绕改变逻辑结果（价格错误、Buffer 越界/分配异常、判断绕过）。
- **负向**：`Number.isSafeInteger` 前置校验 + 边界校验下，边界输入抛异常或被拒绝，逻辑结果不变。
- **回归**：新增数值字段、分页参数、金额/积分换算、Buffer 偏移计算时，复核边界校验与安全整数覆盖。

### 证据引用

- `EVID_NODE_LOGIC_NUMERIC_USER_SOURCE`：用户可控数值进入算术运算的源定位证据
- `EVID_NODE_LOGIC_ARITHMETIC_POINT`：加减乘/长度偏移/货币积分换算等算术运算点证据
- `EVID_NODE_LOGIC_OVERFLOW_IMPACT`：溢出/精度丢失或边界绕过导致逻辑失败/可用性损失的影响证据
