---
name: node-proto-pollution-audit
description: Node.js 原型链污染审计工具。识别递归 merge/clone/assign 中 __proto__/constructor/prototype 键名可控导致的原型污染风险，输出分级、证据与修复建议。
---

# Node.js 原型链污染审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与原型链污染相关的共享抓手（递归合并、深拷贝、JSON 反序列化后键遍历赋值等）
- 若项目存在二次封装的 merge/clone/assign 工具，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、序列化配置、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于**静态证据驱动**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- 递归 merge/clone 汇聚点
- `__proto__` / `constructor` / `prototype` 键名可控
- 污染后 gadget 触发面（选项对象、模板引擎、child_process 选项）

## 枚举规则（强制细化）

- 枚举所有 `merge(`、`extend(`、`Object.assign`、`lodash.merge`、`_.merge`、`deepmerge`、`clone(`、`defaultsDeep` 调用点
- 枚举 JSON 解析后键遍历赋值模式：`for (const k in obj)` + `target[k] = ...`
- 对每个命中点记录：函数来源（原生 / lodash / deepmerge / 项目内封装）、目标对象类型、source 是否来自 `req.body` / `req.query` / `req.params` / JSON.parse 结果
- 记录键名过滤机制：是否显式检查 `__proto__`、`constructor`、`prototype`，或是否依赖 schema 白名单
- 记录污染后可能触发的 gadget：Express 选项对象、模板引擎配置、`child_process` 选项、JWT 算法配置等
- 若存在二次封装的 merge/clone/assign 工具，必须逐层展开其内部实现

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 键名过滤 | joi / zod schema 白名单 | 读取 schema 定义与校验入口，确认是否显式拒绝 `__proto__` / `constructor` / `prototype` | 白名单存在且 fail-close（非法键直接拒绝） → ✅ 安全；黑名单可被 Unicode / 大小写 / 数组路径绕过 → ⚠️ 待确认；无过滤 → 🔴 高危 |
| 对象存储隔离 | `Object.create(null)` 或 `Map` 替代普通对象 | 检索 merge / assign / clone 的目标对象创建方式 | 使用 null-prototype 对象或 Map，且下游 gadget 不读取 `Object.prototype` → ✅ 安全；仍使用普通对象 → 🔴 高危 |
| 原型冻结 | `Object.freeze(Object.prototype)` | 检索是否存在且不被绕过（如通过 `Reflect.defineProperty` 或 `constructor.prototype` 重新赋值） | 已冻结且无绕过路径 → ✅ 纵深防御；未冻结或可被绕过 → ⚠️ 待确认 |
| 依赖版本 | `lodash.merge` / `_.merge` / `defaultsDeep` 等 | 查 `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` 中 lodash 版本 | ≥ 4.17.21 且无已知 CVE → ✅ 安全；低于安全版本或版本不明 → ⚠️ 待确认 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入 merge/clone/assign 的 source，且目标对象为普通对象
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

- `EVID_NODE_PROTO_MERGE_SINK` + `EVID_NODE_PROTO_MAGIC_KEY_CONTROL` + `EVID_NODE_PROTO_KEY_FILTER_ABSENT_OR_BYPASS` 三证齐全，且存在可达入口

### ⚠️待验证

- 缺少 `EVID_NODE_PROTO_GADGET_TRIGGER`（污染后 gadget 触发面证据）
- 键名过滤存在但无法确认是否 fail-close 或是否可被绕过
- Source 到 merge/clone/assign 的调用链未完全闭合

### 误报

- 存在有效键名白名单且不可绕过（fail-close）
- 使用 `Object.create(null)` / `Map` 存储不可信键，且下游 gadget 不读取 `Object.prototype`
- `Object.freeze(Object.prototype)` 已启用且无绕过路径
- source 完全来自固定常量 / 枚举映射，无外部可控入口

## 测试建议（强制）

### 正向测试

- 构造 JSON payload `{"__proto__":{"isAdmin":true}}` 或 `{"constructor":{"prototype":{"isAdmin":true}}}`，验证污染是否生效
- 验证污染后 gadget 触发（如 Express 选项、模板引擎配置、`child_process` 参数被篡改）
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造 schema 白名单外键名（`__proto__`、`constructor`、`prototype`），验证是否被明确拒绝
- 构造 Unicode / 数组路径变形（`__proto__`、`constructor.prototype`），验证过滤是否 robust
- 验证 `Object.create(null)` / Map 场景下污染无法传递到普通对象链

### 回归测试

- 修复后复测原始污染 payload，确认目标对象不再被污染
- 复测 schema 拒绝逻辑、null-prototype 对象使用、lodash 升级版本，确认 barrier 仍然生效
- 验证未引入新的绕过路径（如通过 `constructor.prototype` 重新污染）

## 证据引用

- `EVID_NODE_PROTO_MERGE_SINK`
- `EVID_NODE_PROTO_MAGIC_KEY_CONTROL`
- `EVID_NODE_PROTO_KEY_FILTER_ABSENT_OR_BYPASS`
- `EVID_NODE_PROTO_GADGET_TRIGGER`

## 输出

- `node/vuln_audit/proto-pollution_{timestamp}.md`
- `node/vuln_poc/proto-pollution_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
