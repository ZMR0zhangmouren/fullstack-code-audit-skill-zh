---
name: dotnet-filesystem-audit
description: .NET 文件系统操作审计工具。聚焦目录创建、权限、链接、删除、重命名、TOCTOU 与宿主文件系统差异，为 FILE、UPLOAD、WRITE 等链路提供可利用性增强证据。
---

# .NET 文件系统操作审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与目录遍历、链接跟随、TOCTOU、权限继承和删除/移动/复制相关的共享抓手
- 若项目存在 StorageManager、PathHelper、ArchiveManager、SyncService 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于关联触发入口、路径来源与 `route_id`）
- 可选：`auth_audit/auth_mapping_{timestamp}.md`（用于关联后台操作、管理入口与权限边界）
- 可选：`route_tracer/{route_id}/trace_{timestamp}.md` 与 `route_tracer/{route_id}/trace_summary_{timestamp}.md`（可作为文件系统副作用与入口之间的交叉证据，不是前置硬依赖）

重点检查：

- Directory.CreateDirectory、CreateSymbolicLink、File.Move、File.Copy、File.Delete、File.Replace、Directory.Delete 的危险使用方式
- 符号链接、junction、hardlink、网络共享、容器挂载卷、宿主 bind mount 和只读文件系统的行为差异
- 检查与使用分离导致的 TOCTOU，例如 Exists/ACL 检查后再打开、先校验后重命名、先解析后写入
- GetFullPath/realpath 等规范化后的落点是否在后续步骤被重新拼接、重定向或替换
- 临时目录、缓存目录、日志目录、导出目录、上传目录之间的权限继承和跨目录移动
- Windows ACL、Linux chmod/chown、IIS/Kestrel/容器服务账户权限以及 impersonation 行为
- 删除、覆盖、替换和清理逻辑是否可作为链式利用前置条件，例如删除锁文件、替换配置、覆盖计划任务输入

## 重点检查

- File.Move / File.Copy / File.Delete / Directory.Delete 的路径来源与权限控制
- 符号链接（symlink）、硬链接（hardlink）、junction 的创建与解析逻辑
- TOCTOU 竞态：检查文件存在性后再操作的时间窗口
- 临时文件/目录的创建位置、权限继承与清理逻辑
- 容器卷挂载、网络共享路径的信任边界
- ACL 变更操作：SetAccessControl、权限继承修改
- 文件系统操作作为利用链中间环节的价值（写入后触发、删除后替换）

## 证据引用

- EVID_FS_TOCTOU_OR_LINK_BEHAVIOR

## 枚举规则（强制细化）

- 枚举所有 Directory.CreateDirectory、File.Move、File.Copy、File.Delete、File.Replace、Directory.Delete、符号链接创建与解析相关 API
- 优先搜索 temp、cache、upload、export、log、backup、staging、working、quarantine 等目录语义
- 枚举 ACL 变更、权限继承、容器卷挂载、网络共享、junction、symlink、hardlink 的创建和使用位置
- 对每个文件系统操作记录：触发入口、路径来源、竞态窗口、后续链式利用价值

关键证据：EVID_FS_TOCTOU_OR_LINK_BEHAVIOR。

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 文件系统操作点存在且路径来源可控 | File.Move/Copy/Delete/CreateDirectory/符号链接创建等操作点存在且路径来源包含用户输入 | BLOCKED → 无用户输入映射，专项结束 |
| 二级 | TOCTOU/链接可利用 | 检查与操作存在时间窗（TOCTOU），或符号链接/junction/hardlink 可被用于路径重定向 | BLOCKED → 结论降级为 `⚠️环境依赖` |
| 三级 | 权限/宿主环境允许利用 | 运行账户/ACL/容器挂载/宿主语义允许操作实际生效并产生安全影响 | PARTIAL → 仅输出环境依赖风险与复核建议 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中文件系统操作点 + 路径来源为用户输入，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 输入 → 路径规范化 → 文件系统操作 链路；
  2. 验证 TOCTOU 时间窗（Exists→Open、校验→重命名等）或链接跟随（symlink/junction/hardlink）的可利用性；
  3. 评估运行账户/ACL/容器挂载/宿主语义是否允许操作生效；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：操作点存在 + 路径可控 + TOCTOU/链接可利用 + 权限/宿主环境允许。输出 `确认漏洞`。
2. **待确认**：操作点与路径映射存在，但 TOCTOU/链接或权限证据不足。输出 `待确认`。
3. **误报/无风险**：路径来源不可控，或 TOCTOU 时间窗极短不可利用，或权限严格限制。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在文件系统操作入口（Move/Copy/Delete/CreateDirectory/符号链接创建）
  - 操作路径包含用户可控输入
  - 存在 TOCTOU 时间窗或链接跟随可被利用
- **测试用例建议**：
  - Happy Path：正常文件操作成功，越界/非法路径被拦截
  - 边界/歧义：符号链接指向敏感路径、junction 跨卷跳转、TOCTOU 竞态（替换校验后文件）、ACL 继承绕过
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 工作流（输入→执行→输出）

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（操作点确认）**：必须确认创建/移动/删除/替换等文件系统操作点。
- 🔴 **CHECKPOINT B（竞态与链接确认）**：必须明确 TOCTOU 或链接跟随证据是否成立。
- 🔴 **CHECKPOINT C（权限与宿主确认）**：必须记录 ACL/服务账户/容器挂载的实际边界。
- 🛑 **STOP**：若宿主语义与权限证据不完整，结论降级为 `⚠️环境依赖`，禁止强结论。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| TOCTOU 或链接跟随证据不完整 | 补齐检查点与实际操作点时间窗证据 | 降级 `⚠️环境依赖` |
| ACL/运行账户边界不明确 | 补充权限继承与服务账户信息 | 仅输出环境依赖风险与复核建议 |
| 宿主语义差异导致结论冲突 | 分平台记录行为差异 | 采用最保守口径，禁止强结论 |

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

- 反模式：把 Exists/PathCheck 当作最终安全保障。正确做法：评估 TOCTOU 时间窗与后续操作。
- 反模式：忽略 symlink/junction/hardlink 语义差异。正确做法：按平台分别验证链接行为。
- 反模式：不审计 ACL 继承与运行账户权限。正确做法：补齐权限边界证据。
- 反模式：缺少宿主证据却下强结论。正确做法：降级 `⚠️环境依赖`。

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

- vuln_audit/fs_{timestamp}.md
- 可选：vuln_poc/fs_{timestamp}.md（如能构造链接、竞态、覆盖或跨目录写入验证步骤）
