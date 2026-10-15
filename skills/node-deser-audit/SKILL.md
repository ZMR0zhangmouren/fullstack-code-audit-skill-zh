---
name: node-deser-audit
description: Node.js 反序列化审计工具。识别 node-serialize.unserialize、js-yaml.load（unsafe schema）、serialize-javascript、funcster 与 express-session 自定义 deserializer 的函数执行风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js 反序列化审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与反序列化调用点、序列化库与 schema 选择、输入来源、函数执行触发面相关的共享抓手
- 若项目存在 SerializeHelper、SessionCodec、CacheSerializer、MessageDecoder 等二次封装，必须补充到输出中的项目内抓手章节
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

- `node-serialize` 的 `unserialize()`：`_$$ND_FUNC$$_` 标记的函数以 IIFE 立即执行，等价 RCE 原语
- `js-yaml` <4 的 `yaml.load()`：默认 `DEFAULT_FULL_SCHEMA` 支持 `!!js/function` 函数类型；≥4 的 `load` 默认安全 schema，函数类型抛 `YAMLException`
- `serialize-javascript` 反序列化方向：产物含函数体，还原侧若经 `eval`/`new Function` 重建则形成执行链
- `funcster`：VM 沙箱恢复函数，但深拷贝与原型链恢复存在逃逸面
- `express-session` 默认 `JSON.stringify`/`JSON.parse` 存储安全；显式配置 `serializer`/`deserializer` 选项需重点核查
- Redis/Memcached 会话缓存（connect-redis 等）跨服务读取后的二次反序列化污染面
- `JSON.parse` 本身仅解析 JSON 文本，不执行代码（误报边界，见判定规则）

## 枚举规则（强制细化）

- 枚举所有 `unserialize(`、`node-serialize`、`serialize-javascript`、`funcster`、`deserialize(`、`yaml.load(`、`safeLoad(`、`DEFAULT_FULL_SCHEMA`、`DEFAULT_SAFE_SCHEMA`、`!!js/function` 调用点
- 枚举会话与缓存链路：`express-session`、`deserializer`、`serializer`、`connect-redis`、`connect-memcached`、`JSON.parse(`、`eval(`、`new Function`
- 对每个反序列化点记录：库与版本（package.json + lockfile）、schema 显式值、输入来源（req.body/req.headers/cookie/Redis/MQ）、是否含函数类型
- 区分安全方向与危险方向：`JSON.stringify`→`JSON.parse` 纯数据往返安全；`serialize-javascript`→`eval` 还原、`yaml.load` 全 schema、`unserialize` 函数标记为危险方向
- 识别 IIFE 触发面：`_$$ND_FUNC$$_` 函数体后紧跟 `()` 立即调用、`!!js/function` 自动编译执行
- 记录 `express-session` 的 `store` 后端与自定义 `serializer`/`deserializer` 选项，展开到真实还原调用点
- 若存在二次封装，必须逐层展开到真实 `unserialize`/`yaml.load`/`JSON.parse` 调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 安全 schema / 版本 | `js-yaml` ≥4 `load` 默认安全 schema；`{ schema: DEFAULT_SAFE_SCHEMA }` | 确认 js-yaml 版本与 `yaml.load` 的 schema 参数 | ≥4 默认或显式 safe schema → ✅ 安全；<4 默认 `DEFAULT_FULL_SCHEMA` 且输入可控 → 🔴 高危 |
| 数据格式白名单 | `JSON.parse` + ajv/zod/joi 固定 schema | 检查还原前是否强制 JSON 文本与固定 schema 校验 | JSON.parse + fail-close schema 校验 → ✅ 安全；直接还原任意文本 → 🔴 高危 |
| 输入来源控制 | cookie-signature 签名 / HMAC / 内部可信源 | 检查反序列化数据是否有签名校验且密钥非弱值 | 签名校验 fail-close（验签失败拒绝） → ✅ 安全；无签名或密钥泄露 → 🔴 高危 |
| 会话存储配置 | `express-session` 默认 JSON 序列化 | 检查是否配置自定义 `serializer`/`deserializer` 及 store 后端是否二次反序列化 | 默认 JSON.stringify/parse → ✅ 安全；自定义 deserializer 且会话数据可被外部影响 → 🔴 高危 |
| 危险库禁用 | `node-serialize` / `funcster` / `serialize-javascript` 还原侧 | 确认依赖是否存在且反序列化入口可达 | 未安装或入口不可达 → 🟠 待确认；已安装且输入可控 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入不安全反序列化调用或函数执行触发位
- `待确认`：上下文显示可疑模式，但外部输入来源、barrier 行为或调用链不清晰
- `误报`：输入来自固定常量 / 枚举映射，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到外部可控输入进入反序列化 Sink 位的证据 → `确认漏洞`
- 找到固定 schema 映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、schema 校验器、签名验证、还原器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝还原或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_DESER_UNSAFE_CALL` + `EVID_NODE_DESER_INPUT_CONTROL` + 无 `EVID_NODE_DESER_SAFE_ALTERNATIVE`：外部可控数据进入 `node-serialize.unserialize` / js-yaml <4 `yaml.load` / `serialize-javascript` 还原侧
- `EVID_NODE_DESER_UNSAFE_CALL` + `EVID_NODE_DESER_GADGET_REACH`：`!!js/function` 或 `_$$ND_FUNC$$_` IIFE 函数体可达并自动编译执行
- `express-session` 自定义 `deserializer` 且会话数据可被外部影响（cookie 直存 / 跨服务缓存写入）
- Redis/Memcached 缓存值被写入方污染后，读取方以非 JSON 方式还原并触发函数执行

### ⚠️待验证

- 上下文显示可疑模式（如 `unserialize(` 调用），但外部输入来源不清晰（需补 trace 或调用链）
- `funcster` / `serialize-javascript` 已安装，但反序列化还原入口在当前代码中不可达
- Redis/Memcached 会话链路未闭合：无法确认存储值是否含序列化对象及写入方可控性

### 误报

- 反序列化数据仅来自固定常量 / 内部可信源，且签名校验 fail-close（验签失败拒绝还原）
- 使用 `JSON.parse` + ajv/zod/joi 固定 schema 校验：`JSON.parse` 不执行代码，无函数类型触发面
- `js-yaml` ≥4 默认 `load`（安全 schema）解析纯数据 YAML，函数类型抛 `YAMLException`

## 测试建议（强制）

### 正向测试

- 构造确认可利用的 YAML payload：`!!js/function "return require('child_process').execSync('id')"`，验证 js-yaml <4 `yaml.load` 下命令执行
- 构造 node-serialize IIFE payload：`_$$ND_FUNC$$_function(){require('child_process').exec('id')}()`，验证 `unserialize` 立即执行
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 验证 js-yaml ≥4 对 `!!js/function` 抛 `YAMLException`（fail-close）
- 验证 `JSON.parse` 对函数体文本抛语法错误，ajv/zod 对 schema 外字段拒绝
- 验证签名校验对篡改后的会话 cookie 拒绝还原

### 回归测试

- 修复后复测，确认 schema / 签名 barrier 仍然生效
- 复测依赖升级（js-yaml ≥4、移除 node-serialize）后未引入新的还原路径
- 验证新增缓存后端时仍保持 JSON 纯数据往返

## 证据引用

- `EVID_NODE_DESER_UNSAFE_CALL`
- `EVID_NODE_DESER_INPUT_CONTROL`
- `EVID_NODE_DESER_GADGET_REACH`
- `EVID_NODE_DESER_SAFE_ALTERNATIVE`
- 可选叠加：`EVID_NODE_CFG_SECURITY_SWITCH`（schema / 序列化器默认配置证据）、`EVID_NODE_CFG_MIDDLEWARE_ORDER`（session 中间件与还原调用顺序证据）

## 输出

- `node/vuln_audit/deser_{timestamp}.md`
- `node/vuln_poc/deser_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
