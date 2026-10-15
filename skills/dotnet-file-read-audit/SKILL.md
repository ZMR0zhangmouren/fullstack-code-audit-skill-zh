---
name: dotnet-file-read-audit
description: .NET 文件读取与路径穿越审计工具。识别 File、FileStream、PhysicalFileResult 等读取点中的路径控制与目录逃逸风险。
---

# .NET 文件读取审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时至少覆盖与路径来源、规范化、虚拟路径映射、下载接口和文件流读取相关的共享抓手
- 若项目存在 FileProvider、AttachmentService、ExportReader、StorageGateway 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`source_path`
- 可选：`route_mapping/routes_{timestamp}.md` 与 `route_mapping/params_{timestamp}.md`（用于对齐下载/读取入口、参数来源与 `route_id`）
- 可选：`framework_audit/*_{timestamp}.md`（用于补充宿主、静态文件/模板目录和运行时控制面）
- trace-gate 场景下优先消费：`route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline` 执行，当前专项引用的 `route_id` 应与 `cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- Path.Combine、Path.Join、GetFullPath、GetRelativePath、PhysicalFileProvider、IFileProvider 的路径规范化边界
- File.ReadAllText、OpenRead、FileStream、MemoryMappedFile、PhysicalFileResult、VirtualFileResult、StaticFileMiddleware 读取点
- 用户输入控制文件名、相对路径、扩展名、目录段、租户目录或 blob key 时的路径逃逸可能性
- UNC 路径、网络共享、符号链接、junction、容器挂载、大小写差异和 Windows 保留设备名处理
- 读取目标是否包含配置文件、证书、源码、视图文件、日志、上传目录、NuGet 包缓存或 Secrets 文件
- 读取和执行边界，例如读取 Razor/View/程序集/配置是否会进一步影响模板执行、程序集加载或配置注入
- 下载接口的 content-type、content-disposition、缓存头和鉴权条件是否造成额外信息泄露

## 枚举规则（强制细化）

- 枚举 File.ReadAllText、ReadAllBytes、OpenRead、FileStream、PhysicalFileResult、VirtualFileResult、StaticFile 映射、自定义下载器
- 优先搜索 path、file、filename、template、view、config、download、export、doc、attachment 等参数名
- 枚举所有 Path.Combine、GetFullPath、IFileProvider、PhysicalFileProvider、ContentRoot/WebRoot 相关路径拼接逻辑
- 对每个读取点记录：目标根目录、规范化逻辑、鉴权条件、输出方式、是否可能读到配置/源码/证书/日志/上传文件

## Barrier 验证矩阵（强制）

本专项必须对以下 barrier 类型执行验证，按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 标准评估：

| Barrier 类型 | 验证动作 | 判定标准 |
|-------------|---------|---------|
| **路径规范化与基目录锁定** | 读取路径拼接/规范化源码，确认是否使用 `Path.GetFullPath` + 基目录前缀校验，且校验在规范化之后 | 规范化后锁定在基目录内且 fail-close → ✅ 安全；校验在规范化之前（如仅校验输入字符串） → ⚠️ 可绕过；无基目录锁定 → 🔴 高危 |
| **扩展名/文件类型白名单** | 确认是否对读取目标做扩展名或 MIME 类型限制，且白名单为 fail-close | fail-close（未知类型拒绝） → ✅ 安全；黑名单（仅拦截已知危险扩展名） → ⚠️ 可绕过；无限制 → 🔴 高危 |
| **路径遍历过滤** | 确认是否过滤 `..`、空字节、UNC 前缀、符号链接，以及过滤是在规范化前还是后 | 规范化后过滤且覆盖全部逃逸方式 → ✅ 安全；仅字符串替换 `..` → ⚠️ 可绕过；无过滤 → 🔴 高危 |
| **符号链接/junction 解析** | 确认宿主环境是否解析符号链接/junction，用户输入是否可能指向 symlink 实现目录穿越 | 已禁用 symlink 解析或读取前做最终路径解析 → ✅ 安全；允许 symlink 且未做最终路径校验 → ⚠️ 待确认 |
| **鉴权条件** | 确认读取操作前是否有身份/权限校验，且校验与资源归属一致（防 IDOR） | 有严格的身份+资源归属校验 → ✅ 安全；仅有身份校验无资源归属 → ⚠️ 待确认；无鉴权 → 🔴 高危 |
| **读取后续用途边界** | 确认读取内容是否进入模板引擎、配置解析器、命令执行、反序列化等敏感边界 | 读取后仅返回静态内容 → 🟠 需确认 content-type；读取后进入模板/配置/执行 → 🔴 高危 |

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

1. 用户可控路径直接进入 `File.ReadAllText`、`FileStream`、`PhysicalFileResult` 等读取点，且无基目录锁定或路径规范化验证
2. 路径规范化校验在规范化之前执行（如仅校验原始输入字符串），可通过编码/双重路径分隔符绕过
3. 扩展名/文件类型限制为黑名单模式（如仅拦截 `.exe`、`.aspx`），可通过未知扩展名或空字节绕过
4. 读取操作无鉴权或仅有身份校验无资源归属校验，存在 IDOR 读取他人文件的风险
5. 嵌套/递归结构（如多层 FileProvider 封装）中顶层存在校验，但子层未执行同级校验

### 待确认

1. 上下文显示可疑模式（如 `PhysicalFileResult` 调用），但外部输入来源不清晰（需补 trace 或调用链）
2. Barrier 函数（如基目录校验）存在，但当前分支是否调用、返回值是否被使用无法确认
3. 异步 / 队列 / 事件链路（如消息队列处理文件下载请求）中的参数传递未闭合
4. 宿主环境差异（Windows/Linux 路径解析、symlink 行为）未核清

### 误报

1. 最终路径来自固定常量 / 枚举映射，未知路径会拒绝执行（fail-close）
2. 递归所有层级均复用同一基目录锁定校验器，且校验器为 fail-close
3. 路径规范化后严格锁定在基目录内，且有扩展名白名单（fail-close）与身份+资源归属校验
4. 用户输入仅影响文件名（无目录段），且文件名经过严格的 allowlist 校验

## 测试建议（强制）

遵循 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的测试要求，对每个确认漏洞或待验证项给出：

- **正向测试**：构造路径穿越输入（如 `../../../etc/passwd`、`..\windows\win.ini`、`....//....//etc/hosts`、空字节截断 `%00`），验证文件读取确实存在
- **负向测试**：构造被 barrier 拦截的输入（如基目录外路径、黑名单扩展名、超长路径、非法编码），验证保护机制有效
- **回归测试**：修复后复测，确认 barrier 仍然生效，且未引入新的绕过路径（如双重编码、符号链接、大小写绕过）

测试用例应标注 `test_id`，并在审计报告中与对应命中 ID 关联。

## 证据引用

- EVID_FILE_RESOLVED_TARGET
- EVID_FILE_PATH_NORMALIZATION
- EVID_FILE_EXECUTION_BOUNDARY

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（读取点确认）**：必须确认真实读取 API 与触发入口。
- 🔴 **CHECKPOINT B（路径闭合确认）**：必须给出 `输入路径 -> 规范化 -> 最终目标` 三段证据。
- 🔴 **CHECKPOINT C（边界确认）**：必须说明读取后是否进入模板/配置/执行边界。
- 🛑 **STOP**：若最终目标路径不可证实，结论降级为 `⚠️待验证/环境依赖`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 路径规范化链不完整 | 补齐 `输入 -> normalize -> final path` 证据 | 降级 `⚠️待验证/环境依赖` |
| 宿主解析差异（symlink/junction/UNC）未核清 | 按平台分别验证路径解析语义 | 采用最保守结论并保留验证步骤 |
| 读取后续用途不明 | 追踪到模板/配置/执行边界 | 若仍未闭合，仅输出可疑影响 |

🔴 **STOP：任一兜底触发时，禁止输出“无风险”强结论。**

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

- 反模式：仅凭 `..` 命中就下路径穿越结论。正确做法：证明规范化后最终落点越界。
- 反模式：忽略符号链接/junction/UNC 差异。正确做法：按宿主环境验证解析语义。
- 反模式：不检查读取后续用途。正确做法：确认是否进入模板/配置/执行边界。
- 反模式：证据不足写“无风险”。正确做法：降级为 `⚠️待验证/环境依赖`。

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

- vuln_audit/file_{timestamp}.md
- 可选：vuln_poc/file_{timestamp}.md（已确认 / 待验证 / 环境依赖 PoC；如不适合直接构造请求，至少给出验证步骤）
