---
name: node-vuln-scanner
description: Node.js npm 依赖漏洞扫描器。枚举 package.json 与 lockfile，产出依赖漏洞、typosquatting、生命周期脚本、协议风险与版本漂移清单。
---

# Node.js npm 依赖漏洞扫描

## 共享抓手索引引用

- 本 Skill 的枚举关键字、优先对象与记录口径以 `skills/shared/NODE_AUDIT_GRABBER_INDEX.md` 为单一真源，重点使用其“安全配置抓手”中“依赖清单”章节。
- 路径与产物命名遵循 `skills/shared/IO_PATH_CONVENTION.md` 中 `node/` 子树约定。
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围。
- 排除规则：`node_modules/` 不纳入源码审计面；`package-lock.json`、`yarn.lock`、`pnpm-lock.yaml` 等 lockfile 必须纳入供应链审计面。

## 输入依赖

用户提供：

- `node_source_path`：Node.js 项目、仓库根目录或包含 `package.json` 的目录（必需）。
- `package.json`：项目依赖声明文件（必需）。
- lockfile：`package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` 中至少一种（强烈建议；缺失时版本漂移与 locked 版本判定降级为 `待验证`）。
- `node/stack_detect/stack_detect_{timestamp}.md`：阶段 0 技术栈检出结果（可选，用于确认包管理器类型与 workspace 结构）。
- 可选：`offline_audit_report`（用户注入的离线扫描报告——`yarn audit --json` 输出；提供时解析（包,版本,漏洞ID,严重级）与本地依赖清单 join 并入结论，产物单独列出「来自注入报告的命中」与「来自内置知识的命中」两组）

## 枚举规则（强制细化）

1. **依赖清单枚举**：
   - 全量读取 `package.json` 中的 `dependencies`、`devDependencies`、`optionalDependencies`（含 `peerDependencies` 建议记录）。
   - 每条记录必须包含：名称、版本区间（range）、lockfile 中的 locked 版本。
   - 缺失 lockfile 时，locked 版本标记为 `N/A（待验证）`。

2. **已知漏洞比对**：
   - 环境允许时建议执行 `npm audit --json` 或 `osv-scanner`（作为外部工具建议，skill 自身不含代码）。
   - 不允许访问外部漏洞库或无法执行工具时，按离线 CVE/GHSA 清单人工比对并标注 `待验证`。
   - 命中漏洞必须记录：CVE/GHSA 编号、影响版本区间、当前/locked 版本、严重等级、修复版本建议。

3. **typosquatting/依赖混淆**：
   - 识别名称与主流 npm 包高相似度的依赖（字符替换、增删字符、大小写混淆、作用域前缀伪造）。
   - 相似度判定以 npm registry 流行度（下载量/发布时间/维护活跃度）为基准：与高流行度包名高相似的未知名依赖须标注 `待验证` 并人工复核；允许查询 registry 或参考 lockfile 中同源包分布辅助判断。
   - 识别作用域包（`@scope/pkg`）未锁定 registry（未配置 `.npmrc` 的 `registry=` 或 `@scope:registry=`）的情况。
   - 命中项标记 `风险等级` 与 `人工复核建议`。

4. **生命周期脚本**：
   - 全量列出 `package.json` 中 `scripts` 的 `preinstall`、`install`、`postinstall` 条目。
   - 对每条生命周期脚本进行人工判读，识别下载远程脚本、编译原生模块、修改系统路径、执行外部命令等敏感行为。
   - 同时记录各依赖包内 `node_modules/<pkg>/package.json` 中的生命周期脚本（如 lockfile 携带该信息，或允许访问已安装依赖时）。

5. **协议风险**：
   - 枚举依赖声明或 lockfile 中使用非 https 协议的依赖：
     - `git+http://` 协议依赖（明文传输，高风险，与 `http://` 同等对待）。
     - `git+https://` / `git+ssh://` 协议依赖（传输层加密，需来源可信度校验，结论可低于 `待验证` 但须记录来源声明位置）。
     - `http://` 协议依赖。
     - `file:` 协议依赖（本地路径引用）。
   - 记录协议类型、来源声明位置、是否可替换为安全来源。

6. **版本漂移**：
   - 逐条比对 `package.json` 中的版本 range 与 lockfile 中的 locked 版本。
   - 列出所有 `package.json range` 与 `lockfile locked` 不一致项，包括：
     - lockfile 版本超出 range 声明范围（lockfile 损坏/手动篡改迹象）。
     - range 为通配符（`*`、`x`、空）导致锁定版本不可控。
   - 额外记录 `lockfile 长期未更新导致 locked 版本显著落后于 range 内最新可解析版本` 作为**维护性风险**（非 range/locked 不一致）。

## 判定规则（强制细化）

| 结论 | 判定条件 | 记录要求 |
| ---- | ---- | ---- |
| **已确认** | 存在已知 CVE/GHSA 命中当前 locked 版本，且有 lockfile 或工具输出佐证 | 记录 CVE/GHSA、影响版本、当前版本、修复版本、source_file:line |
| **待验证** | 无法执行外部扫描工具、缺少 lockfile、版本区间无法解析、或命中 typosquatting 需人工复核 | 明确标注 `待验证`，记录缺失证据与补证动作 |
| **误报/不适用** | 依赖为纯类型声明无运行时影响、漏洞仅影响未使用平台/API、或已确认版本不在影响区间内 | 记录排除依据，禁止仅写“无风险” |

- 命中任一协议风险（`git+http://`、`http://`、`file:`）且无法证明来源可信时，结论不得低于 `待验证`。
- 生命周期脚本存在下载/执行外部代码行为且未经显式人工复核时，结论不得低于 `待验证`。
- 存在 typosquatting/依赖混淆嫌疑时，必须保持 `待验证` 直至人工确认包来源。

## 输出

按 `skills/shared/IO_PATH_CONVENTION.md` 中 Node.js 产物路径落盘：

| 产物 | 物理路径 |
| ---- | ---- |
| 依赖漏洞扫描报告 | `node/vuln_scanner/npm_audit_{timestamp}.md` |
| 阶段索引 | `node/vuln_scanner/index_{timestamp}.md` |
| 空结果说明（如适用） | `node/vuln_scanner/empty_result_{timestamp}.md` |

- SBOM 输出（可选增强）：`@cyclonedx/cyclonedx-npm` 生成 `vuln_report/{project_name}_sbom.cdx.json`（CycloneDX）；`spdx-sbom-generator` 对应 SPDX。工具不可用时记 `sbom_status=NOT_RUN + 原因`。
- 产物头部必含 `knowledge_cutoff_date: {YYYY-MM-DD|unknown}`（内置知识声明截止日期，unknown 时伴「结论可能滞后」声明）与 `offline_report_source: {路径|none}`；无注入报告且无在线比对时必须声明「未做在线比对」。

### npm_audit_{timestamp}.md 最小字段

- `pkg_id`：依赖唯一序号。
- `name`：包名（含作用域）。
- `version_range`：`package.json` 声明版本区间。
- `locked_version`：lockfile 解析版本；无 lockfile 时写 `N/A（待验证）`。
- `registry`：安装的 registry 来源（如可确定）。
- `known_vulns`：命中 CVE/GHSA 列表；无则写 `无确证`。
- `typosquatting_flag`：`YES/NO/待验证`。
- `lifecycle_scripts`：`preinstall` / `install` / `postinstall` 全量列表。
- `protocol_risk`：`git+` / `http://` / `file:` / 无。
- `version_drift`：`YES/NO`，不一致时记录 range 与 locked 的具体差异。
- `conclusion`：`已确认` / `待验证` / `不适用`。
- `next_action`：修复、升级、人工复核、离线补证。

### 输出前自检

- [ ] `dependencies` / `devDependencies` / `optionalDependencies` 已全量枚举。
- [ ] lockfile 已纳入解析；缺失时相关字段标记 `待验证`。
- [ ] 生命周期脚本 `preinstall` / `install` / `postinstall` 已全量列出。
- [ ] 协议风险 `git+` / `http://` / `file:` 已逐项记录。
- [ ] 版本漂移对比项已逐条列出。
- [ ] 所有 `已确认` 结论均有 CVE/GHSA 或工具输出支撑。
