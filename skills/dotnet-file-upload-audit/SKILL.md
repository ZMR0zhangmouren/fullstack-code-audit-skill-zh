---
name: dotnet-file-upload-audit
description: .NET 文件上传审计工具。识别 IFormFile、Multipart 处理、保存路径与文件名校验逻辑中的任意上传和可执行上传风险。
---

# .NET 文件上传审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与 IFormFile、multipart、内容类型、文件名、落盘路径和后续消费相关的共享抓手
- 若项目存在 UploadService、StorageProvider、MediaManager、TempFileHelper 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐上传入口、文件参数与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充宿主、静态资源目录和后处理链控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- IFormFile.CopyTo/CopyToAsync、MultipartReader、自定义 Stream 写入、第三方上传组件与对象存储 SDK 的保存点
- 文件名、扩展名、双扩展名、大小写绕过、尾部点/空格、Unicode 同形异义、路径分隔符和目录穿越片段处理
- MIME、Content-Type、文件签名、魔数检测、图像重编码、压缩包、Office/PDF 宏与脚本载荷识别逻辑
- 保存目录是否位于 web root、静态文件目录、临时目录、容器共享目录、CDN 同步目录或可被后台任务二次处理的目录
- 上传后是否可通过 URL 直接访问、经下载接口访问、被图像处理/模板渲染/杀毒/转码组件二次消费
- 重命名策略、唯一文件名生成、租户隔离目录、元数据记录与回滚/删除逻辑是否可靠
- Form 绑定、GraphQL Upload、SignalR 流式上传、大文件分片上传与 resumable upload 场景的鉴权与校验一致性

## 枚举规则（强制细化）

- 枚举所有 IFormFile、IFormFileCollection、MultipartReader、分片上传、对象存储直传回调、自定义上传服务入口
- 优先搜索 upload、file、attachment、avatar、image、document、import、chunk、resume、multipart 等参数名
- 枚举文件名生成、扩展名校验、魔数校验、图像重编码、压缩包检查、Office/PDF 安全检查链
- 对每个保存点记录：保存目录、访问方式、是否进入 web root、是否被后台任务或模板/转码服务再次消费

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 上传入口存在且可触达 | IFormFile/Multipart/直传等入口存在且用户可实际触发上传 | BLOCKED → 无上传入口，专项结束 |
| 二级 | 文件名校验/路径控制可绕过 | 扩展名/MIME/魔数/路径校验存在绕过可能（双扩展/Unicode/目录穿越/大小写） | BLOCKED → 结论降级为 `⚠️待验证/环境依赖` |
| 三级 | 上传后可访问/可执行 | 文件保存后可经 URL/下载/包含/转码/后台任务访问或执行 | PARTIAL → 仅输出绕过假设与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中上传入口 + 文件名/路径/内容来源可控，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 文件名解析 → 校验链 → 保存路径 链路；
  2. 验证扩展名/MIME/魔数/路径校验的绕过条件（双扩展、Unicode 同形、目录穿越、大小写）；
  3. 评估保存后是否可经 URL/下载/包含/转码/后台任务访问或执行；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：上传入口可触达 + 校验可绕过 + 上传后可访问/可执行。输出 `确认漏洞`。
2. **待确认**：上传入口存在但校验绕过或后处理链证据不足。输出 `待确认`。
3. **误报/无风险**：上传入口不存在，或文件名/路径不可控且校验严格、保存后不可访问。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在文件上传入口（IFormFile/Multipart/对象存储直传回调）
  - 文件名、扩展名或保存路径包含用户可控输入
  - 校验链可被绕过或缺失
- **测试用例建议**：
  - Happy Path：正常文件上传成功，非法扩展名/MIME 被拦截
  - 边界/歧义：双扩展名（`shell.aspx.jpg`）、Unicode 同形（`ѕһеll.jsp`）、目录穿越（`../../shell`）、尾部点/空格绕过
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用

## 证据引用

- EVID_UPLOAD_DESTPATH
- EVID_UPLOAD_FILENAME_EXTENSION_PARSING_SANITIZE
- EVID_UPLOAD_ACCESSIBILITY_PROOF

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（上传入口确认）**：必须确认上传入口、文件参数与鉴权条件。
- 🔴 **CHECKPOINT B（落盘链确认）**：必须给出 `文件名/扩展 -> 保存路径 -> 最终可达性` 证据。
- 🔴 **CHECKPOINT C（后处理确认）**：必须说明是否进入转码/模板/扫描/发布等后续消费链。
- 🛑 **STOP**：若无法确认保存目录可达性或执行边界，结论降级为 `⚠️待验证`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 无法确认保存目录与访问面 | 补齐落盘目录、访问路径与鉴权条件 | 降级 `⚠️待验证` |
| 文件校验链不完整（扩展/MIME/魔数） | 分阶段核对校验逻辑与绕过点 | 仅输出待验证风险，不做不可利用结论 |
| 后处理链证据缺失 | 追踪到转码/模板/发布等消费环节 | 保留高风险假设并给验证步骤 |

🔴 **STOP：任一兜底触发时，禁止输出“不可利用”强结论。**

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

- 反模式：只看扩展名白名单就判安全。正确做法：同时检查魔数、重命名策略与可访问性。
- 反模式：忽略双扩展与 Unicode 同形绕过。正确做法：按规范化文件名统一校验。
- 反模式：不审计上传后处理链。正确做法：追踪到转码/模板/发布等二次消费。
- 反模式：证据不足仍判“不可利用”。正确做法：降级 `⚠️待验证`。

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

- vuln_audit/upload_{timestamp}.md
- 可选：vuln_poc/upload_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
