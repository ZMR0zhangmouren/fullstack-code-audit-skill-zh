---
name: dotnet-deser-audit
description: .NET 反序列化审计工具。识别 BinaryFormatter、NetDataContractSerializer、Newtonsoft.Json TypeNameHandling、LosFormatter 等危险反序列化路径。
---

# .NET 反序列化审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与类型信息、多态解析、序列化器选择、KnownType 白名单和输入源相关的共享抓手
- 若项目存在 SerializerHelper、MessageCodec、CacheSerializer、StateFormatter 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐入口、反序列化输入来源与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充宿主、序列化配置和运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- BinaryFormatter、NetDataContractSerializer、SoapFormatter、LosFormatter 的任何使用（高危禁用类）
- Newtonsoft.Json TypeNameHandling != None 的配置（全局或局部）
- 反序列化输入来源：HTTP Body、Cookie、Session、缓存、消息队列、上传文件、ViewState
- SerializationBinder / KnownTypes 白名单是否完整且不可绕过
- 多态类型反序列化：接口/抽象类作为参数类型时的类型解析
- Gadget 链可达性：项目依赖中是否存在已知 Gadget 类型
- 遗留 WebForms ViewState 的 MAC 校验与加密配置

## 证据引用

- EVID_DESER_CALLSITE
- EVID_DESER_INPUT_SOURCE
- EVID_DESER_OBJECT_TYPE_MAGIC_TRIGGER_CHAIN

## 枚举规则（强制细化）

- 枚举 BinaryFormatter、NetDataContractSerializer、SoapFormatter、LosFormatter、ObjectStateFormatter、Json.NET TypeNameHandling 相关入口
- 优先搜索 Deserialize、TypeNameHandling、SerializationBinder、KnownTypes、AssemblyQualifiedName、ViewState、Session、message payload 等关键字
- 枚举 Cookie、Session、缓存、消息队列、上传文件、API Body、GraphQL/Hub 消息、自定义 RPC 的反序列化链路
- 对每个反序列化点记录：类型信息来源、白名单/黑名单策略、后续副作用链、宿主框架与运行环境

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **类型白名单（KnownTypes / SerializationBinder）** | 读取白名单实现源码，确认是否为 fail-close（未知类型拒绝反序列化） | fail-close（未知类型抛异常/拒绝） → ✅ 安全；黑名单（仅拦截已知危险类型） → ⚠️ 可绕过；无白名单 → 🔴 高危 |
| **TypeNameHandling 配置** | 确认 `Newtonsoft.Json` 的 `TypeNameHandling` 是否为 `None`，或是否为 `Auto`/`All`/`Objects` 且配合了安全的 SerializationBinder | `TypeNameHandling.None` → ✅ 安全；`Auto`/`All`/`Objects` 且无安全 Binder → 🔴 高危；有 Binder 但实现不可见 → ⚠️ 待确认 |
| **高危序列化器禁用** | 确认是否使用了 `BinaryFormatter`、`NetDataContractSerializer`、`SoapFormatter`、`LosFormatter` 等已标记为高危的序列化器 | 未使用 → ✅ 安全；已使用但输入不可控 → 🟠 待确认；已使用且输入可控 → 🔴 高危 |
| **输入来源可控性** | 确认反序列化数据是否来自用户可控输入（HTTP Body、Cookie、Query、上传文件等） | 来自用户可控源 → 🔴 高危（需结合类型 barrier 评估）；仅来自内部缓存/数据库且已校验 → 🟠 待确认；仅来自可信内部源 → ✅ 安全 |
| **Gadget 链可达性** | 检查项目依赖（NuGet 包）中是否存在已知 Gadget 类型（如 `ObjectDataProvider`、`PSObject`、`TextFormattingRunProperties` 等） | 无已知 Gadget → 🟠 需结合类型 barrier；有已知 Gadget 且类型 barrier 可绕过 → 🔴 高危 |
| **ViewState MAC/加密** | 确认遗留 WebForms ViewState 是否启用了 MAC 校验与加密 | 启用 MAC+加密 → ✅ 安全；仅启用 MAC 无加密 → ⚠️ 待确认；均未启用 → 🔴 高危 |
| **反序列化后副作用链** | 追踪反序列化后的对象是否触发 `OnDeserialized`、`ISerializable`、`IDisposable`、属性 setter、依赖注入等副作用 | 无副作用链 → 🟠 需确认；有副作用链进入命令执行/文件操作/数据库 → 🔴 高危 |

🔴 **STOP：任一 barrier 验证为 `silent-fallback` 或 `fail-open` 时，禁止将结论标记为「已确认安全」或「误报」。**

## 二阶段判定（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

1. **阶段一（临时结论）**：对每条命中先标记 `确认漏洞候选` / `待确认` / `误报`
2. **阶段二（强制追证）**：
   - 若阶段一为 `确认漏洞候选` → 必须完成 Barrier 验证矩阵全部相关项，通过后才能标记 `已确认`
   - 若阶段一为 `待确认` → 必须向下追至少一跳调用链或下游解析器，直到可判定为止
   - 若阶段二仍无法闭合 → 保持 `待确认`，并明确记录缺失哪一跳证据

## 判定规则（强制细化）

### 确认漏洞

至少满足以下任一条件：

1. 用户可控输入进入 `BinaryFormatter.Deserialize` 等高危序列化器，且无类型白名单或白名单为 fail-open
2. `Newtonsoft.Json` 的 `TypeNameHandling` 为 `Auto`/`All`/`Objects` 且无安全的 `SerializationBinder`
3. 类型白名单为黑名单模式（仅拦截已知危险类型），可通过未知 Gadget 类型绕过
4. 项目依赖中存在已知 Gadget 类型，且类型 barrier 可绕过
5. 嵌套/递归结构（如多层 SerializerHelper 封装）中顶层存在校验，但子层未执行同级校验
6. 反序列化后对象进入命令执行、文件操作、模板渲染等敏感副作用链

### 待确认

1. 上下文显示可疑模式（如 `Deserialize` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如 `SerializationBinder`）存在，但实现不可见或当前分支是否调用无法确认
3. 异步 / 队列 / 事件链路（如消息队列消费反序列化数据）中的参数传递未闭合
4. Gadget 链可达性受依赖版本影响，需确认具体版本是否存在已知 Gadget

### 误报

1. 反序列化输入仅来自固定常量 / 内部可信源，用户无法影响反序列化数据
2. 递归所有层级均复用同一 fail-close 类型白名单校验器
3. `TypeNameHandling.None` 且无动态类型解析逻辑
4. 高危序列化器仅在内部使用，输入完全不可控且无法通过任何外部入口影响

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造包含恶意类型的反序列化 payload（如 `ObjectDataProvider` gadget），验证 RCE/命令执行确实存在
- **负向测试**：构造被 barrier 拦截的输入（如未知类型、不在 KnownTypes 中的类型），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径（如新增 gadget、Binder 绕过）

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。


## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（入口确认）**：必须先确认反序列化调用点与输入来源。
- 🔴 **CHECKPOINT B（类型链确认）**：必须给出类型信息来源与绑定策略（Binder/KnownTypes/TypeNameHandling）。
- 🔴 **CHECKPOINT C（副作用确认）**：必须说明对象落地后是否触发敏感副作用链。
- 🛑 **STOP**：若无法闭合“输入→反序列化→副作用”链，结论降级为 `⚠️待验证`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 仅命中 Deserialize 调用，输入来源不明 | 回溯到 HTTP/消息/缓存等输入边界 | 降级 `⚠️待验证`，保留可疑调用点 |
| 类型控制链不完整（Binder/KnownTypes） | 补齐类型解析与白名单约束证据 | 不输出 RCE 强结论，仅给验证路径 |
| 副作用链未闭合 | 追踪到命令/文件/模板/数据库等后续操作 | 仅输出潜在影响与补证要求 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认可利用”。**

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每次产出前至少执行 2 条典型测试用例（happy path + 边界/歧义场景各 1 条），并记录预期与实际差异。
- 默认要求 `full_test >= 1`；若只能 `dry_run`，必须在结论中标记 `confidence=LOW`，并给出补测计划与负责人。
- 通过标准：关键字段齐全、证据链可回溯、结论级别与门禁状态一致；任一失败则禁止标记“已通过/可交付”。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如“首先/其次/最后/综上/说白了/换句话说”）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出“确认可利用/可交付”。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

- 反模式：只见 Deserialize 调用就下 RCE 结论。正确做法：闭合输入来源、类型控制与副作用链。
- 反模式：忽略 Binder/KnownTypes/TypeNameHandling 约束。正确做法：验证类型边界是否可绕过。
- 反模式：把历史高危组件当当前可利用。正确做法：结合运行时路径与依赖版本判断可达性。
- 反模式：证据链缺口被写成“无风险”。正确做法：降级 `⚠️待验证` 并记录缺失证据。

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如“可能有风险/建议关注/视情况而定/大概率”等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

最小输出片段（可直接复用）：

```md
- 命中ID：M{hash}（文件路径片段+行号+序号，用于跨阶段追踪和回归对齐）
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- test_id：T{hash}（关联测试用例）
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```

## 输出

- vuln_audit/deser_{timestamp}.md
- 可选：vuln_poc/deser_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
