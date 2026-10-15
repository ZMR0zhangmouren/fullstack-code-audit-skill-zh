---
name: dotnet-supply-chain-audit
description: .NET 供应链安全审计工具。扫描 NuGet 包版本、已知 CVE/Advisory 匹配、依赖传递链分析、不安全协议和私有源安全。
---

# .NET 供应链安全审计

## 共享抓手索引引用

- 默认以 shared/DOTNET_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/DOTNET_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- 默认遵循 `skills/shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、测试要求）
- 枚举时覆盖与供应链相关的配置、依赖声明、安全开关抓手
- 供应链安全涉及：包版本管理、依赖传递链、NuGet 源配置、开发/运行时依赖分离、签名验证
- 若项目存在私有源、统一包管理平台或内部包仓库，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- `source_path`：.NET 项目、解决方案或仓库根目录（必需）。
- `route_mapping` / `route_tracer`：上游产物（如存在），用于评估漏洞依赖的运行时可达入口；确认依赖可用且时间戳一致。
- `framework_audit`：框架专项产物（如存在），用于交叉确认依赖使用面。
- 缺失上游产物时，漏洞可达性判定降级为 `⚠️待验证` 并记录缺失证据清单。

## 工作流（输入→执行→输出）

1. 输入：读取 `source_path` 与上游产物（如 `route_mapping` / `route_tracer` / `framework_audit`），确认依赖可用且时间戳一致。
2. 执行：按“共享抓手索引 → 本专项枚举规则 → 证据点引用”顺序完成审计，记录命中点、证据链与未闭合路径。
3. 输出：按本文件“输出”章节落盘到约定路径，结论需标注 `已确认` / `⚠️待验证`，并附缺失证据清单。

## 检查点设计（强制）

- 🔴 **CHECKPOINT A（依赖清单确认）**：必须确认 NuGet/SDK/工具链完整 SBOM。
- 🔴 **CHECKPOINT B（来源完整性确认）**：必须确认包源可信、签名/哈希校验与锁定策略。
- 🔴 **CHECKPOINT C（构建流水线确认）**：必须确认 CI/CD 中的凭据隔离与产物可追溯。
- 🛑 **STOP**：若关键依赖来源无法验证，结论降级为 `⚠️高不确定性`。

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

- 反模式：只看直接依赖忽略传递链。正确做法：追踪到可利用的完整依赖路径。
- 反模式：把 CVE 命中直接等同可利用。正确做法：结合调用面与部署上下文评估。
- 反模式：忽视私有源与签名策略。正确做法：核对源可信度、签名与哈希校验。
- 反模式：关键来源未验证仍下强结论。正确做法：降级 `⚠️高不确定性`。

## 失败场景与兜底（if-then）

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| 依赖清单不完整（缺 lock/传递依赖） | 补齐 SBOM 与依赖图来源 | 结论降级 `⚠️高不确定性` |
| 漏洞命中缺少调用面证据 | 关联到受影响组件与运行时路径 | 不输出可利用强结论，仅给优先级建议 |
| 包源可信度与签名策略不明 | 核对 source、签名、哈希与 CI 策略 | 保留高不确定性并给补证清单 |

🔴 **STOP：任一兜底触发时，禁止输出“已确认可利用供应链风险”。**

- **NuGet 包版本扫描**：
  - 解析 *.csproj、Directory.Packages.props、Directory.Build.props、packages.config、NuGet.lock.json、NuGet.Config
  - 识别直接依赖与传递依赖版本、固定版本 vs 浮动版本 vs 范围版本
  - 标记版本范围中的最高允许版本是否仍存在已知漏洞

- **外部数据库对接工具（环境允许时优先使用，skill 自身不含代码）**：
  - `dotnet list package --vulnerable`：.NET 8+ 内置，基于 NuGet Audit 源输出存在已知漏洞的直接/传递依赖（输出含 CVE 编号与受影响的版本区间）。
  - `osv-scanner --format json --lockfile NuGet.lock.json`（或扫 packages.lock.json / *.csproj）：离线/在线比对 OSV 数据库，输出 JSON 可直接作为 EVID_SUPPLY_TOOL_OUTPUT 证据。
  - 离线路径：下载 OSV 数据库导出（all.zip / NuGet ecosystem 子集），osv-scanner `--offline-vulnerabilities` 参数消费；或按 NuGet.lock.json 逐包查 NuGet Advisory（`https://api.nuget.org/v3-flatcontainer/` 与 advisory 源）人工比对并标注 `待验证`。
  - 工具输出必须记录：工具名、命令、输出摘要（EVID_SUPPLY_TOOL_OUTPUT），禁止仅以工具结论替代可达性判定。

- **已知 CVE/Advisory 匹配**：
  - 对接 NVD/NuGet Advisory API/GitHub Advisory Database/OWASP Top 10 for .NET
  - 识别受影响版本区间、修复版本、漏洞类型（远程代码执行、拒绝服务、信息泄露、权限提升）
  - 区分 CVSS 3.1 等级：严重 Critical（9.0-10.0）、高危 High（7.0-8.9）、中危 Medium（4.0-6.9）、低危 Low（0.1-3.9），与 skills/shared/SEVERITY_RATING.md 等级映射表对齐

- **依赖传递链分析**：
  - 追踪传递依赖的可利用路径：直接依赖 → 传递依赖 → 最终可利用接口
  - 识别"幽灵依赖"：未在 csproj 中显式声明但实际被引用的包
  - 识别"测试依赖"：仅在 Test 项目中的依赖是否泄露到运行时
  - 识别"开发依赖"：DotNetCliToolReference、BuildDependsOn、MSBuild 任务依赖

- **不安全协议风险**：
  - 识别 http:// 源 vs https:// 源（中间人攻击风险）
  - 识别非官方或第三方 NuGet 源（包篡改风险）
  - 识别不带完整性校验（hash/Signature）的包源

- **私有 NuGet 源安全**：
  - 识别 V3/V2 协议私有源、认证方式（API Key / Azure Artifacts / nuget.config）
  - 检查 nuget.config 或 Directory.Build.props 中的凭据硬编码或环境变量引用
  - 识别内部包是否包含敏感 PDB、XML 文档或调试符号

- **签名与完整性验证**：
  - 识别 NuGet 包签名验证配置（trustedSigners、allowUntrustedRoot）
  - 检查是否启用 Signed Package Verification
  - 识别社区包 vs 微软官方包的签名差异

- **过时组件风险**：
  - 识别已停止维护的包（EOL、no longer maintained）
  - 识别版本冻结（frozen lockfile）在新漏洞出现时的暴露窗口
  - 识别 .NET 版本与包兼容性：不兼容的包版本可能导致运行时异常或安全回退

- **开发工具链风险**：
  - 识别 MSBuild Task 注入风险：自定义 MSBuild Task 执行位置
  - 识别 Source Link、Debug Type、PDB 文件中的源码路径泄露
  - 识别 Build-InlineTask、UsingTask 动态加载风险

## 枚举规则（强制细化）

- **依赖声明文件枚举**：
  - 搜索关键字：*.csproj、PackageReference、PackageVersion、<ProjectReference>、Directory.Packages.props、packages.config、NuGet.lock.json、NuGet.Config、nuget.config
  - 记录：直接依赖名/版本、传递依赖名/版本、固定版本策略、版本范围、浮动版本策略
  - 识别 ImplicitlyExpandDesignTimebuildTargets、TreatAsLocalPackage、IsShippingPackage

- **漏洞匹配枚举**：
  - 搜索关键字：nuget.org advisory、CVE-*、GHSA-*、security advisory、NuGet.Security.Advisories
  - 记录：CVE ID、CVSS 评分、漏洞类型、受影响版本区间、修复版本、补丁链接
  - 识别 package name + version tuple 是否在已知漏洞数据库中

- **传递依赖路径枚举**：
  - 搜索关键字：<Dependency>、TransitiveProjectReference、ProjectAssetsFile、NuGet.DepencyGraph
  - 记录：依赖层级、可利用传递路径、直接/传递依赖区分、作用域（compile/runtime/test/build/custom）
  - 识别 IsImplicitlyDefined、PrivateAssets、IncludeAssets、ExcludeAssets

- **源配置枚举**：
  - 搜索关键字：<packageSources>、<add key=、<clear />、http://、https://、<credential>、<dotnet nuget>
  - 记录：源 URL、协议类型、认证方式、是否官方源、是否私有源、是否本地源
  - 识别 packageSourceMap、restoreSources、fallbackFolders

- **签名验证枚举**：
  - 搜索关键字：trustedSigners、allowUntrustedRoot、SignedPackageVerification、nuget verify、--signature
  - 记录：签名验证配置、可信签名者、证书链验证、是否验证来源
  - 识别 AllowAuthorUnsingedPackages、AllowUntrustedRoot 风险

- **开发工具链枚举**：
  - 搜索关键字：MSBuildTask、UsingTask、BuildDependsOn、SourceLink、DebugType、Embed、PDB
  - 记录：Task 源、Task 执行位置、是否动态加载、PDB 文件路径、源码链接暴露
  - 识别 InlineTask、DynamicLoad 风险

- **过时组件枚举**：
  - 搜索关键字：EOL、no longer maintained、deprecated、legacy、<legacyPackageAllowDuringBuild>、frozen lockfile
  - 记录：包名、最后发布日期、维护状态、.NET 版本兼容性、已知安全问题
  - 识别 version frozen 在新漏洞出现时的暴露窗口

- 对每个有漏洞的依赖记录：包名、版本、CVSS 评分、漏洞类型、受影响入口/路由、传递依赖路径、修复版本建议

## Barrier 验证矩阵（强制）

按 `DOTNET_AUDIT_EXECUTION_STANDARD.md` 的 fail-close 三级标准评估：

| 等级 | 检查项 | 通过标准 | 失败降级 |
|------|--------|----------|----------|
| 一级 | 存在 NuGet/依赖声明 | *.csproj/packages.config/NuGet.lock.json 中存在依赖声明 | BLOCKED → 无依赖声明文件，专项结束 |
| 二级 | 存在已知 CVE/不安全源/签名缺失 | 依赖版本匹配已知 CVE、使用 http:// 源/非官方源、allowUntrustedRoot 启用 | BLOCKED → 所有依赖版本安全、源可信、签名验证完整，结论降级 |
| 三级 | 漏洞依赖在运行时可达且可被利用 | 存在漏洞的传递依赖在运行时加载、且可通过项目代码路径触达漏洞接口 | PARTIAL → 仅输出潜在风险与验证步骤 |

## 二阶段判定流程（强制）

- **阶段 1（初筛命中）**：命中依赖声明 + CVE/不安全源/签名问题 + 运行时可达性，输出 `命中ID：M{hash}`。
- **阶段 2（精筛确认）**：
  1. 逆向追踪 依赖声明 → 版本 → CVE 数据库匹配 链路；
  2. 验证 NuGet 源协议（http vs https）、签名验证配置（trustedSigners/allowUntrustedRoot）；
  3. 评估漏洞依赖的传递路径与运行时可达性（是否通过项目代码路径可触达漏洞接口）；
  4. 若三级 Barrier 全部通过 → `确认漏洞`；任一失败 → 按矩阵降级。

## 判定规则与优先级（强制）

1. **确认漏洞**：依赖声明存在 + 已知 CVE/不安全源/签名缺失 + 运行时可达且可利用。输出 `确认漏洞`。
2. **待确认**：依赖声明存在但 CVE 影响版本或运行时可达性证据不足。输出 `待确认`。
3. **误报/无风险**：所有依赖版本无已知 CVE、使用 https 官方源、签名验证启用、无 untrusted root、漏洞依赖不可达。输出 `误报` 并给出判定依据。

## 测试建议与最小触发条件（强制）

- **最小触发条件**：
  - 存在 *.csproj/packages.config/NuGet.lock.json 等依赖声明
  - 依赖版本匹配已知 CVE 或使用 http:// 源/非官方源
  - 或签名验证禁用（allowUntrustedRoot）
- **测试用例建议**：
  - Happy Path：正常依赖版本无 CVE、使用 https 官方源、签名验证通过
  - 边界/歧义：传递依赖 CVE 利用路径、版本范围浮动导致漏洞版本引入、私有源凭据硬编码、MSBuild Task 注入
- 每条命中输出追加 `命中ID：M{hash}` 和 `test_id：T{hash}`，用于回溯。

## 证据引用

- EVID_SUPPLY_CVE_MATCH：依赖版本与已知 CVE/GHSA 数据库命中记录证据（CVE ID、影响版本区间、当前/locked 版本、修复版本）
- EVID_SUPPLY_UNSAFE_SOURCE：包源协议或来源风险证据（源 URL、协议类型、认证方式）
- EVID_SUPPLY_SIGNATURE_GAP：签名验证缺失或配置缺陷证据（allowUntrustedRoot、trustedSigners 未配置）
- EVID_SUPPLY_TRANSITIVE_PATH：传递依赖可利用路径证据（直接依赖 → 传递依赖 → 可利用接口）
- EVID_SUPPLY_SPOOF_DEP：依赖混淆/typosquatting/幽灵依赖嫌疑证据（包名相似度、来源声明位置）
- EVID_SUPPLY_TOOL_OUTPUT：工具扫描原始输出证据（dotnet list package --vulnerable / osv-scanner / npm audit）
- EVID_SUPPLY_LOCK_GAP：lockfile 缺失或版本漂移证据（声明位置、range、locked 版本）

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

- 输出文件：vuln_audit/supply_chain_{timestamp}.md
- 必须按 依赖清单与版本分布、已知漏洞匹配、传递依赖风险、源配置与协议安全、签名验证、开发工具链风险、过时组件 七个章节组织结果
- 每个漏洞包必须写明 包名、版本、CVSS 评分、漏洞类型、受影响入口/路由（如有）、传递依赖路径、修复版本建议、优先级（P0/P1/P2）
- 必须单列 高危供应链风险（P0）、中危供应链风险（P1）、低危供应链风险（P2）、待评估组件 四类
- 必须列出 无法修复的依赖冲突（版本互斥）与缓解措施
- 若通过 `dotnet-audit-pipeline` 执行，应同步生成 `vuln_report/{project_name}_nuget_vuln_report_{timestamp}.md`
- 若发现私源配置问题，必须在 项目内抓手 章节记录 nuget.config 位置与凭据配置方式
- SBOM 输出（可选增强，具备工具时执行）：`dotnet list package --format json` 或 CycloneDX .NET 工具生成 `vuln_report/{project_name}_sbom.cdx.json`（CycloneDX）；SPDX 需求场景输出 `*.spdx.json`。SBOM 须覆盖直接+传递依赖、锁定版本、许可信息（如可获取）。生成工具不可用时记 `sbom_status=NOT_RUN + 原因`。