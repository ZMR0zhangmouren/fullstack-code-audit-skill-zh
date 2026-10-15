---
name: dotnet-tpl-audit
description: .NET 模板注入审计工具。识别 Razor Runtime Compilation、自定义模板引擎、邮件模板、动态视图解析中的模板名或模板内容可控风险。
---

# .NET 模板注入审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与模板来源、运行时编译、局部模板、邮件模板和预览渲染相关的共享抓手
- 若项目存在 TemplateRenderer、MailComposer、PreviewEngine、ViewCompiler 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐模板入口、参数绑定与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充 Razor、邮件模板或运行时编译控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- Razor Runtime Compilation：用户是否能控制模板内容或模板路径
- 第三方模板引擎（RazorLight、Scriban、Fluid、DotLiquid）：模板来源可控性
- 邮件模板：模板内容从数据库/CMS 加载且管理员可编辑
- CMS/低代码平台：用户自定义模板的编译与执行权限
- 模板中的服务容器访问：是否能通过模板调用任意服务方法
- Include/Import/Partial：模板路径可控导致的文件包含
- 模板编译缓存：是否存在缓存投毒或持久化后门风险

## 证据引用

- EVID_TPL_ENGINE_RENDER_OR_PARSE_ENTRY
- EVID_TPL_TEMPLATE_OR_EXPR_CONTROL
- EVID_TPL_EXEC_CHAIN_ENTRY

## 枚举规则（强制细化）

- 枚举 Razor Runtime Compilation、自定义 ViewEngine、邮件模板、CMS 模板、导出模板、通知模板和低代码模板引擎
- 优先搜索 template、view、layout、partial、render、compile、razor、liquid、scriban、mustache 等关键名称
- 枚举模板名、模板路径、模板内容、helper、include/import、模型对象和服务容器访问能力
- 对每个模板入口记录：模板来源、编译方式、运行时权限、输出落点、是否存在用户可控模板或表达式

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **模板来源可控性** | 确认模板内容/模板路径是否来自用户可控输入（如用户上传、管理后台编辑、URL 参数指定模板名） | 用户可控模板内容/路径且无沙箱 → 🔴 高危；仅管理员可编辑且管理员受信任 → 🟠 需确认；模板完全固定 → ✅ 安全 |
| **运行时编译权限** | 确认 Razor Runtime Compilation 或第三方模板引擎的运行时编译是否开启，编译后的代码执行权限 | 运行时编译开启且模板可控 → 🔴 高危；运行时编译关闭 → ✅ 安全；编译在沙箱中 → 🟠 需确认沙箱强度 |
| **Helper/函数白名单** | 确认模板中可访问的 helper、函数、服务容器是否为 fail-close 白名单 | fail-close 白名单 → ✅ 安全；无白名单或黑名单模式 → 🔴 高危；白名单不可见 → ⚠️ 待确认 |
| **Include/Import/Partial 路径限制** | 确认模板中的 include/import/partial 路径是否来自用户可控输入，是否限制在模板目录内 | 路径可控且无基目录锁定 → 🔴 高危；路径固定或 sandbox 锁定 → ✅ 安全 |
| **模板编译缓存安全** | 确认模板编译缓存是否可被投毒（如用户可控模板写入缓存后被其他用户触发） | 缓存键与用户输入关联且模板可控 → 🔴 高危；缓存隔离且模板固定 → ✅ 安全 |
| **输出落点与回显** | 确认模板渲染结果是否进入邮件发送、PDF 生成、页面展示等可被攻击者感知的输出面 | 进入攻击者可感知的输出面 → 🔴 高危放大；仅内部预览或管理员可见 → 🟠 需确认 |

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

1. 用户可控输入直接进入模板内容/模板路径，且无沙箱/白名单限制
2. 运行时编译开启且模板内容可控，可执行任意 C# 代码
3. Helper/函数白名单为 fail-open 或 silent-fallback，模板可调用危险函数（如文件操作、命令执行）
4. Include/Import/Partial 路径来自用户可控输入，且无基目录锁定（文件包含）
5. 嵌套/递归结构（如多层 TemplateRenderer 封装）中顶层存在校验，但子层未执行同级校验
6. 模板编译缓存可被用户可控模板投毒

### 待确认

1. 上下文显示可疑模式（如 `RenderTemplate` 调用），但模板来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如 helper 白名单）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路（如后台邮件渲染）中的参数传递未闭合
4. 运行时编译配置分散在多处，无法确认是否开启

### 误报

1. 最终模板来自固定常量 / 枚举映射，未知输入会拒绝执行（fail-close）
2. 递归所有层级均复用同一 fail-close 模板白名单校验器
3. 运行时编译关闭，模板仅预编译且内容完全固定
4. 模板渲染结果不进入任何攻击者可感知的输出面

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造模板注入 payload（如 `@(new System.Diagnostics.ProcessStartInfo("calc"))`、`{% include '/etc/passwd' %}`、自定义 helper 调用文件操作），验证模板执行确实存在
- **负向测试**：构造被 barrier 拦截的输入（如白名单外 helper、非法模板路径、超长度模板），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。


## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（模板引擎识别）**：必须确认 Razor/Scriban/Handlebars 等引擎与渲染入口。
- 🔴 **CHECKPOINT B（数据流确认）**：必须确认用户输入是否进入模板语句、helper、表达式求值。
- 🔴 **CHECKPOINT C（隔离与白名单确认）**：必须确认 helper 白名单、函数禁用与沙箱边界。
- 🛑 **STOP**：若模板执行能力与输入可控性未同时判定，不得下“不可利用”结论。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 模板入口明确但可控性不清 | 补齐模板名/内容来源映射证据 | 降级 `⚠️待验证` |
| helper/include 能力边界不明确 | 核对白名单与禁用策略 | 不输出不可利用强结论 |
| 渲染结果去向不明 | 追踪到页面/邮件/导出等输出面 | 保守评估并保留待补证项 |

🔴 **STOP：任一兜底触发时，禁止输出“不可利用”。**

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

- 反模式：只看到模板引擎就判模板注入。正确做法：确认模板内容/模板名是否可控。
- 反模式：忽略 include/import 与 helper 能力。正确做法：评估可调用面与沙箱边界。
- 反模式：不追踪渲染产物去向。正确做法：确认是否进入邮件、页面或可执行消费链。
- 反模式：证据不全写“不可利用”。正确做法：降级并列出缺失证据。

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

- vuln_audit/tpl_{timestamp}.md
- 可选：vuln_poc/tpl_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
