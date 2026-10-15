---
name: dotnet-archive-extract-audit
description: .NET 归档解压路径穿越审计工具。识别 ZipArchive、Tar、SharpCompress 等解压逻辑中的 entry name 逃逸与最终目标路径越界风险。
---

# .NET 归档解压审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与压缩包格式、条目名、解压目录、覆盖策略、软链接和后续消费相关的共享抓手
- 若项目存在 ArchiveService、PackageImporter、PluginInstaller、BackupRestore 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充宿主、静态文件目录、上传/插件目录与运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

重点检查：

- ZipArchive、Tar、SharpCompress、第三方解压组件的 extract 调用点与目标目录来源
- ZipArchiveEntry.FullName、entry.Key、tar path 等归档条目名是否包含 ../、绝对路径、盘符、UNC、保留设备名等逃逸片段
- 条目名在规范化、替换分隔符、去前导斜杠、大小写归一化后的最终解析目标是否仍越出 base directory
- 解压目录是否位于 web root、插件目录、模板目录、任务输入目录、可下载目录或后台扫描目录
- 压缩包中的符号链接、硬链接、重复文件名、目录覆盖、文件替换和压缩炸弹防护是否处理
- 解压结果是否会被后续模板渲染、程序集加载、脚本执行、配置读取或静态资源发布链消费

## 重点检查

- ZipFile.ExtractToDirectory、ZipArchive 逐条目解压、SharpZipLib、SharpCompress、TarFile 等解压 API 的调用点与条目名来源
- 归档条目名（entry.FullName）是否包含 `../` 或绝对路径，是否在解压前做规范化与目录约束校验
- 解压目标目录是否为 Web 可访问目录、可执行目录或配置目录
- 符号链接条目、超长路径条目、重复文件覆盖的处理逻辑
- 用户上传归档文件后的解压链路：上传 → 暂存 → 解压 → 落盘 → 后续消费
- 插件/主题/模板导入功能中的归档解压是否有白名单或沙箱隔离

## 证据引用

- EVID_ARCHIVE_EXTRACT_CALLSITE
- EVID_ARCHIVE_ENTRY_NAME_SOURCE
- EVID_ARCHIVE_FINAL_TARGET

## 枚举规则（强制细化）

- 枚举 ZipArchive、Tar、SharpCompress、SevenZip 封装、自定义解压服务、导入功能中的 extract 调用点
- 优先搜索 extract、unzip、untar、archive、entry、restore、import package、theme/plugin import 等业务语义
- 枚举 entry name 规范化、目标目录拼接、重复文件覆盖、软链接/硬链接条目处理逻辑
- 对每个解压点记录：archive 来源、目标目录、最终解析路径、解压后文件是否进入可访问或可执行区域

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准执行：

| # | 校验项 | 通过标准 | 未通过处理 |
|---|--------|----------|------------|
| B1 | Source 可控性 | 入口参数（上传文件名/归档内容）可被攻击者控制 | 来源不可控 → 标记 `NO_FINDING`，结束 |
| B2 | Sink 可达性 | 解压 API（ZipFile.ExtractToDirectory/SharpCompress/TarFile）在路由可达路径上 | 不可达 → 标记 `NO_FINDING`，结束 |
| B3 | 边界校验缺失 | 条目名未做规范化、目录约束或前缀校验 | 有充分校验 → 标记 `NO_FINDING`，结束 |

**fail-close 规则：任一 Barrier 未通过即终止判定，禁止继续输出漏洞结论。**

## 二阶段判定流程

1. **阶段一：结构命中**
   - 命中 archive 解压调用点（ZipArchive/SharpCompress/TarFile）
   - 确认 entry name 来源于用户可控输入
   - 判定：若来源不可控 → `NO_FINDING`；继续则进入阶段二

2. **阶段二：语义确认**
   - 确认 entry name 包含路径逃逸片段（`../`、绝对路径、UNC、盘符）
   - 确认规范化/目录约束校验缺失或可被绕过
   - 确认最终解析路径越出 base directory
   - 判定：若任一条件不成立 → 降级为 `NO_FINDING` 或 `PENDING_VERIFICATION`

3. **结论输出**
   - 满足阶段一 + 阶段二 → `FOUND`
   - 阶段一通过但阶段二未完全确认 → `PENDING_VERIFICATION`
   - 阶段一未通过 → `NO_FINDING`

## 判定规则

| 条件组合 | 结论 | 等级建议 |
|----------|------|----------|
| B1=PASS ∧ B2=PASS ∧ B3=PASS ∧ 阶段二确认路径越界 | `FOUND` | 🔴 高 |
| B1=PASS ∧ B2=PASS ∧ B3=UNCERTAIN | `PENDING_VERIFICATION` | 🟡 中 |
| B1=FAIL ∨ B2=FAIL | `NO_FINDING` | 🟢 无 |
| 有校验但可绕过 | `FOUND` (注明绕过路径) | 🟠 中高 |

## 测试建议（强制）

- 构造含 `../` 路径的 ZIP/TAR 条目，验证解压后文件是否落出目标目录
- 构造含绝对路径、UNC 路径、Windows 保留设备名（`CON`、`NUL` 等）的归档条目
- 构造符号链接条目，验证是否被正确处理或跟随
- 在 Windows/Linux 双平台验证路径解析差异
- 每次验证记录 `test_id：T{hash}`，关联到对应 `命中ID：M{hash}`

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按"共享抓手索引 → 本专项枚举规则 → 证据点引用"顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件"输出"章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（入口确认）**：开始前必须确认归档来源、解压目标目录和触发入口（`route_id`/功能点）已明确。
- 🔴 **CHECKPOINT B（路径闭合）**：输出前必须给出 `entry name -> 规范化 -> 最终目标路径` 三段证据链。
- 🔴 **CHECKPOINT C（影响面确认）**：若解压结果涉及 web root/插件/模板/配置目录，必须单列影响面与可达性。
- 🛑 **STOP**：若最终目标路径无法证实是否越界，结论必须降级为 `⚠️待验证/环境依赖`，禁止输出"已确认可利用"。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 无法获取 `entry -> normalize -> final path` 三段证据 | 回到调用点补齐路径解析与规范化过程证据 | 标记 `⚠️待验证/环境依赖`，并保留待补证项 |
| 宿主平台差异导致路径结论不一致（Windows/Linux/UNC） | 分平台分别验证并记录差异条件 | 结论按最保守口径降级，不输出已确认可利用 |
| 无法确认解压落点可达性（webroot/插件/模板） | 补充目录暴露与后续消费链证据 | 保留风险假设并输出验证步骤，不做强结论 |

🔴 **STOP：任一兜底触发时，禁止输出"已确认可利用"。**

## 资源引用与可达性校验（强制）

- 必引共享索引：`skills/shared/DOTNET_AUDIT_GRABBER_INDEX.md`（抓手来源）与 `skills/shared/EVIDENCE_POINT_IDS.md`（证据口径）。
- 输出口径校验：落盘路径与命名必须对齐 `skills/shared/IO_PATH_CONVENTION.md`，不得自定义偏离目录。
- 证据一致性校验：若引用分级结论，需与 `skills/shared/SEVERITY_RATING.md` 保持一致。
- 可达性检查：提交前至少确认一次关键引用文件可访问（例如 `DOTNET_AUDIT_GRABBER_INDEX.md`、`IO_PATH_CONVENTION.md`）。

## 实测用例与通过标准（强制）

- 每次产出前至少执行 2 条典型测试用例（happy path + 边界/歧义场景各 1 条），并记录预期与实际差异。
- 默认要求 `full_test >= 1`；若只能 `dry_run`，必须在结论中标记 `confidence=LOW`，并给出补测计划与负责人。
- 通过标准：关键字段齐全、证据链可回溯、结论级别与门禁状态一致；任一失败则禁止标记"已通过/可交付"。

## 整体架构与冗余控制（强制）

- 章节组织必须保持三层骨架：`输入约束` → `执行步骤` → `输出与验收`，不得缺层或跨层混写。
- 单段建议不超过 6 行；同义规则禁止重复出现两次以上，重复内容需合并到唯一真源章节。
- 禁止 AI 腔与空话衔接词堆叠（如"首先/其次/最后/综上/说白了/换句话说"）；发现即改为可执行语句。

## 质量门禁与评估一致性（强制）

- 产出前必须执行最小门禁自检：`输入完整性`、`关键证据命中`、`输出路径合法` 三项全部为 PASS。
- 若存在 `关键证据缺失`、`链路未闭合`、`consistency_check_status=BLOCKED` 任一条件，结论必须降级为 `BLOCKED`，禁止输出"确认可利用/可交付"。
- 报告中必须显式记录：`gate_status`、`blocked_reasons`、`recheck_action`，并与 `quality/*` 产物可回溯对齐。

## 不要做的事（反例黑名单）

- 反模式：仅凭 `../` 关键字命中直接判高危。正确做法：必须给出 `entry -> normalize -> final path` 闭合链。
- 反模式：忽略 Windows 盘符、UNC、绝对路径与大小写归一化差异。正确做法：按宿主平台分别验证路径约束。
- 反模式：未确认解压后落点可达性就给利用结论。正确做法：补充 webroot/插件/模板/配置目录影响面证据。
- 反模式：把"证据不足"写成"无风险"。正确做法：统一降级为 `⚠️待验证/环境依赖` 并保留待补证项。

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如"可能有风险/建议关注/视情况而定/大概率"等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

最小输出片段（可直接复用）：

```md
- 审计结论等级：已确认
- 命中ID：M{hash}
- test_id：T{hash}
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```

## 输出

- vuln_audit/archive_{timestamp}.md
- 可选：vuln_poc/archive_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
