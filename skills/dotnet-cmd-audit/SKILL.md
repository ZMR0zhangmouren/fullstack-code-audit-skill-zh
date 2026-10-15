---
name: dotnet-cmd-audit
description: .NET 命令执行审计工具。识别 Process.Start、shell 参数拼接与脚本执行风险，输出可利用性分级、PoC 与修复建议。
---

# .NET 命令执行审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与命令构造、shell 选择、参数传递、工作目录、环境变量相关的共享抓手
- 若项目存在 ShellHelper、JobRunner、ScriptExecutor、DeployManager 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充宿主平台、外部命令运行环境与运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- Process.Start、ProcessStartInfo.FileName、Arguments、ArgumentList、UseShellExecute、Verb 等调用点
- cmd.exe、powershell.exe、pwsh、bash、sh、wscript、cscript、msbuild、dotnet tool 等间接执行链
- 用户输入进入命令名、参数、工作目录、环境变量、脚本文件路径或标准输入的路径
- 是否使用 ProcessStartInfo.ArgumentList 安全分隔参数，还是退回到整条命令行字符串拼接
- 文件上传、导出、压缩、图像处理、备份、git/svn/hg 操作、ffmpeg、wkhtmltopdf 等常见外部工具调用
- Windows 与 Linux 宿主差异、引号规则、转义规则、空格与 shell 元字符处理差异
- 低权限服务账户、容器、沙箱、AppLocker、ConstrainedLanguageMode 等缓解条件是否真实存在

## 枚举规则（强制细化）

- 枚举所有 Process.Start、ProcessStartInfo、cmd/powershell/bash 包装器、自定义脚本执行服务
- 优先搜索 FileName、Arguments、ArgumentList、UseShellExecute、RedirectStandardInput、WorkingDirectory、EnvironmentVariables
- 枚举文件转换、备份恢复、git/svn、压缩解压、图像处理、PDF 生成、诊断脚本、CI/CD helper 这类常见外部命令调用业务
- 对每个执行点记录：命令构造方式、参数来源、是否经过白名单、宿主平台、服务账户权限、输出是否回显

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **整串拼接（Arguments）** | 读取 `ProcessStartInfo.Arguments` 构造源码，确认是否来自字符串拼接/插值 | 外部可控输入参与拼接且无常量前缀限制 → 🔴 高危；固定命令+仅用户参数可控 → 🟠 需进一步验证参数位 |
| **ArgumentList 分隔** | 确认是否使用 `ArgumentList.Add()` 替代整串拼接，并检查有无混入整串（如 `ArgumentList.Add($"-flag {input}")`） | 正确使用且无整串混入 → ✅ 安全；混用或单参数位含插值 → ⚠️ 待确认 |
| **UseShellExecute** | 确认 `UseShellExecute = true` 时 `FileName` 和 `Arguments` 的 shell 解释路径 | 用户输入进入 `FileName` 或 shell 元字符未转义 → 🔴 高危；固定命令+固定参数 → ✅ 安全 |
| **命令白名单** | 读取白名单实现源码，确认是否为 fail-close（未知命令拒绝执行） | fail-close（枚举外拒绝/抛异常） → ✅ 安全；fail-open（默认允许/回退） → ⚠️ 可绕过；无白名单 → 🔴 高危 |
| **路径/工作目录穿越** | 确认 `WorkingDirectory` 或脚本路径是否来自用户输入，是否限制在基目录内 | 用户输入可穿越到 `/etc`、`C:\Windows`、`.ssh` 等敏感目录 → 🔴 高危；固定路径或 sandbox 锁定 → ✅ 安全 |
| **环境变量注入** | 确认 `EnvironmentVariables` 是否被用户输入污染，尤其是 `PATH`、`LD_PRELOAD`、`COMSPEC` 等 | 用户可控 → 🔴 高危；仅系统设置 → ✅ 安全 |

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

1. 外部可控参数直接进入 `Arguments`、`FileName`、`WorkingDirectory`、`EnvironmentVariables` 的拼接/插值位置，且无 barrier 验证
2. `UseShellExecute = true` 时用户输入进入 `FileName` 或含 shell 元字符的参数位
3. `ArgumentList` 被错误混用（单参数位内存在字符串插值）
4. 命令白名单为 `fail-open` 或 `silent-fallback`，外部可控输入可绕过白名单进入 Sink
5. 嵌套/递归结构（如多层 helper 封装）中顶层存在校验，但子层未执行同级校验

### 待确认

1. 上下文显示可疑模式（如 `Process.Start` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如白名单、路径校验）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路（如 Hangfire、Quartz、消息队列）中的参数传递未闭合
4. `ArgumentList` 与整串拼接混用，但当前调用点无法确认具体使用路径

### 误报

1. 最终命令或标识符来自固定常量 / 枚举映射，未知输入会拒绝执行（fail-close）
2. 递归所有层级均复用同一命令白名单校验器，且白名单为 fail-close
3. 参数通过 `ArgumentList` 安全分隔，且每个参数位均来自固定常量或已验证的白名单输出
4. 运行环境存在真实沙箱/容器隔离，且用户输入无法逃逸到宿主命令执行上下文

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造确认可利用的命令注入输入（如 `; cat /etc/passwd`、`& whoami`、`$(id)`），验证漏洞确实存在
- **负向测试**：构造被 barrier 拦截的输入（如白名单外命令、非法路径穿越、超长参数），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 证据引用

- EVID_CMD_EXEC_POINT
- EVID_CMD_COMMAND_STRING_CONSTRUCTION
- EVID_CMD_USER_PARAM_TO_CMD_FRAGMENT


## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（执行点确认）**：必须先确认真实命令执行点（`Process.Start`/脚本入口）再给风险判断。
- 🔴 **CHECKPOINT B（参数映射确认）**：必须给出 `用户输入 -> 命令片段/参数位` 映射证据。
- 🔴 **CHECKPOINT C（宿主差异确认）**：必须注明 Windows/Linux shell 差异与引号转义边界。
- 🛑 **STOP**：若无法闭合输入到执行链，结论降级为 `⚠️待验证`，禁止输出已确认命令注入。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 无法证明用户输入进入命令片段/参数位 | 回溯参数绑定到 `ProcessStartInfo` 构造链 | 标记 `⚠️待验证`，保留可疑调用点 |
| ArgumentList 与整串拼接混用导致判断不清 | 分别评估参数分隔与 shell 解释路径 | 按高风险路径保守降级，不给确认注入 |
| 宿主与账户边界证据不足 | 补充运行账户、容器与平台差异证据 | 仅输出环境依赖利用假设与验证步骤 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认命令注入”。**

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

- 反模式：把命令关键字命中等同注入成立。正确做法：必须闭合 `输入 -> 参数位 -> 执行点` 证据链。
- 反模式：忽略 ArgumentList 与整串拼接差异。正确做法：分别评估参数分隔与 shell 解释风险。
- 反模式：忽略运行账户与容器隔离影响。正确做法：补充权限边界与后果范围分析。
- 反模式：无 PoC 条件仍下强结论。正确做法：标注 `⚠️待验证/环境依赖`。

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

## 输出

- vuln_audit/cmd_{timestamp}.md
- 可选：vuln_poc/cmd_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
