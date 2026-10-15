---
name: dotnet-xxe-audit
description: .NET XXE 审计工具。识别 XmlDocument、XmlReader、XDocument、XPath 和 XSLT 相关解析场景中的外部实体与 DTD 风险。
---

# .NET XXE 审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 XML 解析器、DTD、XmlResolver、XSLT、schema 导入和外部资源访问相关的共享抓手
- 若项目存在 XmlHelper、ConfigImporter、FeedParser、SoapBridge 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐 XML/SOAP 入口、参数来源与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充 XML 解析配置、宿主与运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- XmlDocument.LoadXml / Load：是否设置 XmlResolver = null
- XmlReader.Create：XmlReaderSettings.DtdProcessing 是否为 Prohibit
- XDocument / XPathDocument：输入来源与解析器配置
- XslCompiledTransform.Load：XSLT 来源可控性与脚本执行
- DataSet.ReadXml / ReadXmlSchema：XML 输入的 DTD 处理
- SOAP/WCF 消息解析：自定义 MessageInspector 中的 XML 处理
- SAML/metadata 导入：外部 IdP 元数据的 XML 解析
- Office/OpenXML 文件解析：上传的 docx/xlsx 内嵌 XML 实体

## 证据引用

- EVID_XXE_PARSER_CALL
- EVID_XXE_INPUT_SOURCE
- EVID_XXE_ENTITY_DOCTYPE_SAFETY_AND_ECHO

## 枚举规则（强制细化）

- 枚举 XmlDocument、XmlReader、XDocument、XPathDocument、XslCompiledTransform、DataSet.ReadXml、SOAP 解析入口
- 优先搜索 LoadXml、CreateReader、DtdProcessing、XmlResolver、Transform、ReadXml、schema、metadata import 等关键调用
- 枚举 HTTP Body、上传文件、消息总线、配置导入、WCF/SOAP、SAML/metadata、Office/OpenXML 二次解析入口
- 对每个解析点记录：安全选项、输入来源、DOCTYPE/Entity 是否允许、结果回显或后续使用路径

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **DtdProcessing 配置** | 确认 `XmlReaderSettings.DtdProcessing` 是否为 `Prohibit`，或 `XmlDocument.XmlResolver` 是否为 `null` | `Prohibit` / `null` → ✅ 安全；`Parse` 或默认允许 → 🔴 高危；配置不可见 → ⚠️ 待确认 |
| **XmlResolver 限制** | 确认是否使用 `XmlSecureResolver` 或自定义受限 Resolver，限制外部实体解析 | 严格限制外部资源 → ✅ 安全；允许任意外部 URI → 🔴 高危；配置不可见 → ⚠️ 待确认 |
| **实体扩展限制** | 确认 `MaxCharactersFromEntities` 是否设置合理上限，防止 Billion Laughs / 实体扩展 DoS | 有合理上限 → ✅ 安全；无限制 → 🔴 高危 |
| **XSLT 外部资源** | 确认 `XslCompiledTransform` 是否允许 `document()` 函数访问外部资源，是否启用脚本执行 | 禁止外部资源/脚本 → ✅ 安全；允许 → 🔴 高危 |
| **输入来源校验** | 确认 XML 输入（HTTP Body/上传文件/SOAP/配置导入）是否经过 schema 校验或签名验证 | 有 schema/签名校验且 fail-close → ✅ 安全；无校验 → 🔴 高危 |
| **结果回显/外联** | 确认实体展开结果是否回显到响应、写入文件、触发外联请求 | 回显/外联可控 → 🔴 高危放大；无回显且无外联 → 🟠 需确认 |

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

1. `DtdProcessing` 为 `Parse` 或默认允许，且 `XmlResolver` 未限制外部实体
2. 用户可控 XML 输入（HTTP Body/上传文件/SOAP）进入解析器，且无 schema/签名校验
3. `XslCompiledTransform` 允许 `document()` 访问外部资源或启用脚本执行
4. 实体扩展无限制，存在 Billion Laughs DoS 风险
5. 嵌套/递归结构（如多层 XmlHelper 封装）中顶层存在安全配置，但子层未执行同级配置

### 待确认

1. 上下文显示可疑模式（如 `LoadXml` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 配置（如 `DtdProcessing`）存在，但当前调用点是否使用该配置无法确认
3. 异步 / 队列 / 事件链路（如消息队列消费 XML）中的参数传递未闭合
4. XSLT 外部资源限制配置分散在多处，无法确认完整行为

### 误报

1. `DtdProcessing` 明确设置为 `Prohibit`，且 `XmlResolver` 为 `null`
2. 递归所有层级均复用同一安全配置（`Prohibit` + null Resolver）
3. XML 输入仅来自可信内部源，且经过严格的 schema 校验 + 签名验证
4. `XslCompiledTransform` 禁止 `document()` 和脚本执行

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造 XXE payload（如 `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>`、Billion Laughs），验证漏洞确实存在
- **负向测试**：构造被 barrier 拦截的输入（如 DTD 被禁止、外部实体解析失败、超过实体扩展限制），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。


## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（解析器配置确认）**：必须确认 DtdProcessing、XmlResolver、实体限制配置。
- 🔴 **CHECKPOINT B（输入面确认）**：必须确认 XML 输入来源与可控边界（HTTP/上传/消息）。
- 🔴 **CHECKPOINT C（回显与外联确认）**：必须确认实体展开结果是否回显、写盘或触发外联。
- 🛑 **STOP**：若安全配置与输入可控性未同时核定，不得宣告 XXE 不成立。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 解析器配置证据不完整 | 补齐 DtdProcessing/XmlResolver/实体限制配置 | 降级 `⚠️待验证` |
| 输入来源边界不明确 | 枚举 HTTP/上传/消息/二次解析入口 | 不输出“无 XXE”结论 |
| 回显与外联链路未闭合 | 追踪到响应/日志/写盘/下游请求 | 保守评估并保留补证清单 |

🔴 **STOP：任一兜底触发时，禁止宣告 XXE 不成立。**

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每个 skill 至少维护 2 个典型测试用例（happy path + 一条复杂场景），并在结果中标注用例 ID。
- 每轮评估至少 1 条用例执行 `full_test`；若受限只能 `dry_run`，必须记录 `dry_run_reason` 与补测计划。
- 通过标准至少同时满足：`意图达成`、`关键证据命中`、`输出格式合规`；任一不满足不得给出“通过”。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如“首先/其次/最后/综上/说白了/换句话说”）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出“确认可利用/可交付”。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

- 反模式：只看默认配置就判安全。正确做法：核对实际解析器实例与运行时选项。
- 反模式：忽略二次解析路径（上传/消息/OpenXML）。正确做法：覆盖所有 XML 输入面。
- 反模式：不检查 XSLT/document() 外联。正确做法：审计扩展能力与资源访问策略。
- 反模式：证据不足直接判“无 XXE”。正确做法：降级并列出待补证据。

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

- vuln_audit/xxe_{timestamp}.md
- 可选：vuln_poc/xxe_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
