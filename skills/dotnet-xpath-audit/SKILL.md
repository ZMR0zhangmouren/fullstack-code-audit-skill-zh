---
name: dotnet-xpath-audit
description: .NET XPath 注入审计工具。识别 XPathNavigator、XPathDocument、XPathExpression 中用户输入到 XPath 查询构造的注入风险，从 XXE 专项拆分。
---

# .NET XPath 注入审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 XML 解析器、XPath 表达式、数据流、用户输入、查询构造相关的共享抓手
- 若项目存在 XmlQueryHelper、XPathHelper、ConfigQuerier、DocumentNavigator 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐 XML 查询入口、参数来源与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充 XML 解析配置、XPath 引擎与运行时控制面）
- 可选：`vuln_audit/xxe_{timestamp}.md`（XPath 注入与 XXE 存在交叉，可复用部分发现）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- XPathNavigator、XPathDocument、XPathExpression 的查询表达式构造
- XmlNamespaceManager 与 XPath 命名空间解析
- 用户输入到 XPath 查询字符串的拼接路径
- XPath 注入 Payload：`' or '1'='1`、`//user[password/text()='xxx']`、`substring(//password,1,1)='a'`
- XML 数据源：Config XML、XML 配置文件、AppSettings、Web.config、appsettings.json
- XPath 查询结果的回显、写入、日志记录
- XmlResolver 在 XPath 查询中的配置（可能导致 XXE 组合利用）

## 枚举规则（强制细化）

- 枚举所有使用 XPathNavigator、XPathDocument、XPathExpression 的代码文件
- 优先搜索 Select、XPathCompile、XPathEvaluate、SelectNodes、SelectSingleNode、Matches、XmlNamespaceManager 等关键调用
- 枚举字符串拼接、插值字符串、String.Format、StringBuilder 构造 XPath 表达式的位置
- 枚举 XML 数据来源：配置文件加载、HTTP 请求 XML Body、SOAP 消息、上传文件、数据库 XML 列、消息队列 XML 消息
- 对每个 XPath 查询点记录：表达式构造方式、参数来源、是否参数化、XPath 引擎版本、XmlResolver 配置

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **XPath 字符串拼接** | 读取 XPath 表达式构造源码，确认是否来自字符串拼接/插值（如 `$"//user[password='{input}']"`） | 用户输入参与 XPath 拼接 → 🔴 高危；固定 XPath 模板 + 参数化值位 → 🟠 需确认值位边界 |
| **XPath 参数化/预编译** | 确认是否使用 `XPathExpression.Compile` + 变量绑定，而非字符串拼接 | 正确使用参数化/变量绑定 → ✅ 安全；参数化与拼接混用 → ⚠️ 待确认；无参数化 → 🔴 高危 |
| **输入转义/白名单** | 确认用户输入进入 XPath 前是否有转义或白名单校验（如仅允许字母数字） | fail-close 白名单 → ✅ 安全；部分转义（如仅转义引号）→ ⚠️ 可绕过；无转义 → 🔴 高危 |
| **XmlResolver 配置** | 确认 `XmlResolver` 是否被禁用或限制，防止 XPath + XXE 组合利用 | 禁用/受限 XmlResolver → ✅ 安全；允许外部实体解析 → ⚠️ 待确认（需 XXE 专项复核） |
| **命名空间管理** | 确认 `XmlNamespaceManager` 是否严格管理命名空间，用户是否可注入命名空间前缀 | 命名空间严格管理 → ✅ 安全；用户可控命名空间前缀 → ⚠️ 待确认 |
| **查询结果敏感语义** | 确认 XPath 查询结果是否进入鉴权、业务决策、回显或写入操作 | 进入鉴权/敏感业务判断 → 🔴 高危放大；仅内部日志记录 → 🟠 需确认 |

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

1. 用户可控输入直接进入 XPath 字符串拼接位置，且无参数化/转义
2. XPath 表达式中使用字符串插值构造查询条件（如 `$"//user[@name='{input}']"`）
3. 输入转义为 fail-open 或 silent-fallback，可通过编码/双重转义绕过
4. XmlResolver 允许外部实体解析，且 XPath 查询可被利用进行 XXE 组合攻击
5. 嵌套/递归结构（如多层 XmlQueryHelper 封装）中顶层存在校验，但子层未执行同级校验
6. XPath 查询结果进入鉴权/敏感业务判断

### 待确认

1. 上下文显示可疑模式（如 `SelectNodes` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如参数化封装）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路中的参数传递未闭合
4. XmlResolver 配置分散在多处，无法确认完整配置行为

### 误报

1. 最终 XPath 表达式来自固定常量，未知输入会拒绝执行（fail-close）
2. 递归所有层级均复用同一 fail-close 输入白名单校验器
3. 用户输入仅进入已严格参数化的值位，XPath 结构完全固定
4. XmlResolver 已禁用外部实体解析，且 XPath 查询无拼接/插值

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造 XPath 注入 payload（如 `' or '1'='1`、`' or ''='`、`//user[password/text()='x' or '1'='1']`），验证注入确实存在
- **负向测试**：构造被 barrier 拦截的输入（如参数化值位外的拼接尝试、非法字符被转义），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

### 强制记录字段

| 字段 | 说明 |
|------|------|
| file_path | 源文件路径 |
| line_number | 行号 |
| xpath_api | 使用的 XPath API 类型 |
| query_construction | 查询构造方式（拼接/参数化） |
| user_input_source | 用户输入来源 |
| input_sanitization | 输入过滤/转义措施 |
| xml_datasource | XML 数据源类型 |
| namespace_usage | 是否使用 XmlNamespaceManager |
| resolver_config | XmlResolver 配置 |
| result_usage | 查询结果使用方式 |
| risk_level | 风险等级（P0-P4） |

## 证据引用

- EVID_XPATH_QUERY_CONSTRUCTION（新增）：XPath 查询构造点
- EVID_XPATH_USER_INPUT_INTO_QUERY（新增）：用户输入流入 XPath 查询
- EVID_XXE_PARSER_CALL：复用 XXE 专项的 XML 解析器调用证据
- EVID_XXE_INPUT_SOURCE：复用 XXE 专项的 XML 输入源证据

## 失败与降级分支（强制）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 找到 XPath 查询点但输入来源不可追踪 | 先输出查询构造证据与可见变量 | 标记 `⚠️来源待验证`，禁止已确认注入结论 |
| 用户输入可控但缺少执行上下文（命名空间/解析器） | 记录 `XmlNamespaceManager/XmlResolver` 配置现状 | 降级为 PARTIAL 并列出缺失配置证据 |
| 与 XXE 证据冲突（解析器配置不一致） | 保留双方证据并标记冲突来源 | 结论降级，等待 framework/xxe 交叉复核 |

🔴 **STOP：缺少“输入→XPath表达式→执行结果”三段证据时，禁止输出已确认漏洞。**

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

| # | 反模式 | 为什么不要做 | 正确做法 |
|---|---|---|---|
| 1 | 把 XXE 证据直接当 XPath 注入证据 | 两者边界不同 | 分开给出解析层与查询层证据 |
| 2 | 只给 payload 不给代码映射 | 不可复核不可修复 | 必须写明 API/行号/变量映射 |
| 3 | 忽略命名空间上下文 | 会误判查询可达性 | 记录 NamespaceManager 与表达式关系 |

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（查询构造确认）**：必须确认 XPath 表达式构造点与输入来源。
- 🔴 **CHECKPOINT B（参数化/转义确认）**：必须确认变量绑定或安全转义策略。
- 🔴 **CHECKPOINT C（数据影响确认）**：必须确认查询结果是否影响鉴权、业务决策或回显。
- 🛑 **STOP**：若表达式构造与防护证据未闭合，不得宣告 XPath 注入不成立。

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

- vuln_audit/xpath_{timestamp}.md
- 可选：vuln_poc/xpath_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC）

### vuln_audit/xpath_{timestamp}.md 结构

```markdown
# XPath 注入审计报告

## 概述
- 审计范围：`source_path`
- 审计时间：{timestamp}
- 发现的 XPath 注入风险点数量：N

## 高风险发现（EVID_XPATH_* 证据引用）
...逐项列出，含文件路径、行号、漏洞描述、风险等级...

## 中风险发现
...逐项列出...

## 低风险发现
...逐项列出...

## 项目内 XPath 相关抓手
...项目特定的二次封装...

## XPath 注入 Payload 参考
### 认证绕过
' or '1'='1
' or ''='

### 数据提取
//element[@attribute='value']
//*/text()
substring(//password,1,1)='a'

### 条件推断
[position()=N]
[count(//element)=N]

## 修复建议
1. 使用参数化 XPath 查询（XPathExpression.SetContext）
2. 输入白名单校验
3. XPath 结果脱敏
4. 禁用 XmlResolver 或使用受限的 XmlUrlResolver
```

## 与 XXE 专项的边界划分

- **本 Skill 职责**：XPath 查询逻辑、表达式构造、用户输入到 XPath 的数据流
- **dotnet-xxe-audit 职责**：XML 解析器配置、外部实体、DTD 处理、XInclude
- **交叉场景**：XmlResolver 配置同时影响 XXE 和 XPath 注入，优先由 XXE 专项覆盖解析器配置，本 Skill 关注 XPath 查询层