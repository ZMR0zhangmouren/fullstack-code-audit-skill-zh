---
name: dotnet-file-write-audit
description: .NET 任意文件写入审计工具。识别用户可控数据进入写入 Sink 的路径，并评估写后可访问性、可包含性与可执行性。
---

# .NET 文件写入审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与路径拼接、目录创建、覆盖写入、临时文件、权限和原子替换相关的共享抓手
- 若项目存在 FileStore、ConfigWriter、ExportService、DocumentWriter 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐写入入口、参数来源与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充宿主、可访问目录和运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- File.WriteAllText、WriteAllBytes、FileStream、StreamWriter、AppendAllText、Save/Export/Generate 报表等写入点
- 用户输入或外部数据如何进入目标路径、文件名、目录段、扩展名或 blob/object key
- Path.Combine/GetFullPath 后是否做 base directory 前缀校验，校验后是否又重新拼接导致绕过
- 写入内容是否来自请求体、模板内容、日志伪造、压缩包解压结果、反序列化数据或远程拉取内容
- 写后文件是否可通过静态资源、下载接口、模板引擎、程序集加载、计划任务或后台作业被进一步消费
- 覆盖、追加、截断、原子替换、临时文件再 rename、权限继承和 ACL 设置是否扩大影响
- 本地磁盘、网络共享、对象存储、容器卷与宿主挂载目录的访问面差异

## 枚举规则（强制细化）

- 枚举所有 WriteAllText、WriteAllBytes、AppendAllText、StreamWriter、Save、Export、Generate、template save、config save 操作
- 优先搜索 path、dest、target、filename、output、export、report、template、config 等目标路径字段
- 枚举路径拼接、临时文件落盘、rename/move、对象存储 key 生成、容器卷挂载落点选择逻辑
- 对每个写入点记录：路径来源、内容来源、覆盖模式、写后访问面、是否可能进入模板/配置/静态资源/程序集消费链

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 写入点存在且路径/内容来源可控 | File.WriteAllText/StreamWriter/Save 等写入点存在且路径或内容来源包含用户输入 | BLOCKED → 无用户输入映射，专项结束 |
| 二级 | 路径校验/过滤可绕过 | Path.Combine/GetFullPath 后的 base directory 校验可被绕过（重新拼接、解码差异、链接跟随） | BLOCKED → 结论降级为 `⚠️待验证/环境依赖` |
| 三级 | 写后可达/可执行 | 写入文件可被静态资源/下载/模板包含/程序集加载/计划任务消费或执行 | PARTIAL → 仅输出保守风险结论与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中写入点 + 路径或内容来源为用户输入，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 输入 → 路径拼接/规范化 → 写入点 链路，同时追踪内容来源；
  2. 验证 base directory 校验、Path.Combine 后重新拼接、符号链接跟随等绕过条件；
  3. 评估写后是否可被静态资源/下载/包含/程序集/任务消费或执行；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：写入点存在 + 路径/内容可控 + 校验可绕过 + 写后可达/可执行。输出 `确认漏洞`。
2. **待确认**：写入点与输入映射存在，但路径校验绕过或写后可达性证据不足。输出 `待确认`。
3. **误报/无风险**：写入点无用户输入映射，或路径校验严格且写后不可达。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在文件写入点（WriteAllText/StreamWriter/Save/Export）
  - 目标路径或写入内容包含用户可控输入
  - 路径校验可被绕过或缺失，且写后文件可访问
- **测试用例建议**：
  - Happy Path：正常路径写入成功，越界路径被拦截
  - 边界/歧义：Path.Combine 后重新拼接绕过、符号链接跟随、临时文件 rename 攻击、编码差异绕过
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用

## 证据引用

- EVID_WRITE_CALLSITE
- EVID_WRITE_DESTPATH_JOIN_AND_NORMALIZATION
- EVID_WRITE_CONTENT_SOURCE_INTO_WRITE
- EVID_WRITE_EXECUTION_ACCESSIBILITY_PROOF

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（写入点确认）**：必须先确认写入调用点与触发入口。
- 🔴 **CHECKPOINT B（路径与内容确认）**：必须同时闭合路径来源与内容来源映射。
- 🔴 **CHECKPOINT C（写后影响确认）**：必须说明写后文件是否可访问、可包含或可执行。
- 🛑 **STOP**：若写后可达性证据缺失，结论降级为 `⚠️待验证/环境依赖`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 路径来源或内容来源未闭合 | 分别补齐路径链与内容链证据 | 降级 `⚠️待验证/环境依赖` |
| 写后可达性不明 | 补充静态资源/下载/任务消费证据 | 不输出高危确认，保留待补证 |
| 临时文件与原子替换链缺失 | 完整追踪落盘与 rename/move 流程 | 仅输出保守风险结论 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认高危”。**

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

- 反模式：只证明“能写文件”就直接判高危。正确做法：补齐写后可访问/可执行证据。
- 反模式：忽略原子替换与临时文件 rename 路径。正确做法：审计完整落盘链。
- 反模式：不区分内容可控与路径可控。正确做法：双链同时闭合再下结论。
- 反模式：证据不足写强结论。正确做法：降级 `⚠️待验证/环境依赖`。

## 可执行参数与输出模板（强制）

- 审计结论等级：`已确认` / `⚠️待验证` / `不适用`（三选一，禁止留空）。
- 证据最小集：至少包含 `入口点`、`可控参数`、`关键调用`、`安全边界`、`缺失证据` 五项。
- 输出文件命名：统一使用 `{topic}_{timestamp}.md`，并与 `IO_PATH_CONVENTION.md` 对齐。
- 禁止使用软化措辞：如“可能有风险/建议关注/视情况而定/大概率”等；证据不足时必须明确写 `⚠️待验证` 与下一步补证动作。

最小输出片段（可直接复用）：

```md
- 审计结论等级：已确认
- 证据最小集：入口点=...；可控参数=...；关键调用=...；安全边界=...；缺失证据=无
- 下一步动作：若存在缺口，补 trace_id=... 的参数传播证据
```

## 输出

- vuln_audit/write_{timestamp}.md
- 可选：vuln_poc/write_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
