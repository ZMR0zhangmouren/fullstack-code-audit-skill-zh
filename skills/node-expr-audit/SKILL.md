---
name: node-expr-audit
description: Node.js 表达式注入审计工具。识别 expr-eval、mathjs.evaluate、jexl、jsonata、vm.runInNewContext、new Function 的求值与沙箱逃逸风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js 表达式注入审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与表达式引擎、求值入口、沙箱配置、规则引擎与计算公式相关的共享抓手
- 若项目存在 RuleEngine、FormulaService、ExpressionEvaluator、ConditionParser 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐表达式入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、规则引擎注册与运行时控制面）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- expr-eval：`Parser.evaluate(expr)` / `new Parser({ functions })` —— 内置函数白名单与自定义函数配置
- mathjs：`math.evaluate(expr, scope)` —— `constructor` 链绕过历史与 scope 暴露面
- jexl：`jexl.eval(expr, context)` —— 属性链访问可沿原型链到达 context 之外的对象
- jsonata：`jsonata(expr).evaluate(input)` —— 表达式能力面与输入数据可达性
- `vm.runInNewContext` / `vm.runInContext`：非安全沙箱，`this.constructor.constructor('return process')()` 逃逸
- `new Function(expr)` / `eval(expr)` / `setTimeout(字符串)` 直接求值不可信输入
- 业务入口：规则引擎、报表公式、营销条件、计算器接口、自定义过滤器与排序配置
- 求值结果进入敏感语义（SQL 查询、文件操作、权限判断）与错误堆栈泄露

## 枚举规则（强制细化）

- 用 rg 枚举：`expr-eval`、`Parser\.evaluate|parser\.evaluate`、`mathjs|math\.evaluate`、`jexl|jexl\.eval`、`jsonata`、`vm\.runInNewContext|vm\.runInContext`、`new Function\(`、`eval\(`、`setTimeout\(['"]`
- 枚举规则配置、公式计算、表达式过滤等入口的表达式来源（请求参数 / 数据库存量配置 / 管理后台）
- 对每个求值点记录：引擎、表达式来源、沙箱 / 函数白名单配置、context 暴露对象、求值结果流向
- 区分"整串可控求值"与"固定模板 + 数值参数位"两种模式
- `vm` 场景必须记录传入的 context 对象内容并评估 `constructor` 链逃逸面
- 若存在二次封装规则引擎，必须逐层展开到真实求值调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 表达式字符串可控性 | `Parser.evaluate(userInput)` / `vm.runInNewContext(拼接串)` | 读取表达式构造源码，确认是否来自用户输入 | 用户输入直接进入求值 → 🔴 高危；固定模板 + 数值参数位 → 🟠 需确认参数位边界 |
| 函数白名单 | expr-eval `{ functions: {...} }`、mathjs `math.import` 限制 | 读取白名单配置源码，确认危险函数是否可达、未知符号是否报错 | fail-close 白名单 → ✅ 安全；黑名单或默认全量 → 🔴 高危；配置不可见 → ⚠️ 待确认 |
| 求值前校验 | 语法 / 长度 / AST 结构校验 | 确认求值前是否有白名单或结构校验且校验器 fail-close | fail-close 校验 → ✅ 安全；仅长度限制 → ⚠️ 可绕过；无校验 → 🔴 高危 |
| 沙箱隔离 | `vm.runInNewContext(code, ctx)` | Node vm 非安全沙箱，检查 ctx 是否暴露 `constructor` 链可达对象 | 用 vm 处理不可信输入 → 🔴 高危（可逃逸）；仅受信代码 → 🟠 需确认 |
| context 暴露面 | jexl context / mathjs scope | 检查传入对象是否冻结、是否包含 `process` / db / exec 等敏感对象 | 最小化且冻结 → 🟠 低风险面；暴露敏感对象 → 🔴 高危 |
| 求值结果敏感语义 | 结果进入 SQL / 文件 / 权限判断 | 追踪求值结果流向 | 进入敏感语义 → 🔴 高危放大；仅数值计算且不回显 → 🟠 需确认 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入表达式求值或沙箱内执行
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

- `EVID_NODE_EXPR_EVALUATE_POINT` + `EVID_NODE_EXPR_STRING_CONCAT` + 无有效 `EVID_NODE_EXPR_SANDBOX_CONFIG`
- 不可信输入直接进入 `vm.runInNewContext` / `new Function` / `eval` 求值
- jexl / mathjs 经 `constructor` 链或 context 原型访问 `process` 等危险对象，白名单为 fail-open
- 求值结果进入 SQL / 文件 / 权限判断等敏感语义且表达式可控

### ⚠️待验证

- 上下文显示可疑模式（如 `Parser.evaluate` 调用），但外部输入来源不清晰（需补 trace 或调用链）
- 沙箱 / 白名单配置存在，但当前分支是否调用、配置是否生效无法确认
- 表达式来源复杂（数据库存量配置 / 缓存 / 管理后台），无法确认是否可被用户影响

### 误报

- 表达式来自固定常量 / 枚举映射，未知输入会拒绝执行（fail-close）
- 用户输入仅进入数值参数位，表达式结构完全固定且无字符串插值
- 求值引擎配置了 fail-close 函数白名单，且 context 无敏感对象暴露

## 测试建议（强制）

### 正向测试

- 构造表达式逃逸 payload：`constructor.constructor('return process')().exit()`、jexl 原型链访问、mathjs `import` 尝试
- 验证整串可控求值场景下任意表达式执行成立
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造被 barrier 拦截的输入：白名单外函数、非法语法、超长表达式
- 验证 fail-close 白名单下未知符号报错而非静默执行
- 验证冻结 context 下原型链访问被阻断

### 回归测试

- 修复后复测，确认白名单与 context 最小化仍然生效
- 升级 expr-eval / mathjs / jexl 版本后复测默认沙箱行为未变化
- 验证新增规则配置入口仍走统一求值封装

## 证据引用

- `EVID_NODE_EXPR_EVALUATE_POINT`
- `EVID_NODE_EXPR_STRING_CONCAT`
- `EVID_NODE_EXPR_SANDBOX_CONFIG`

## 输出

- `node/vuln_audit/expr_{timestamp}.md`
- `node/vuln_poc/expr_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
