---
name: node-archive-extract-audit
description: Node.js 归档解压路径穿越（Zip Slip）审计工具。识别 unzipper/adm-zip/yauzl/extract-zip/tar-stream 解压链路中 entryName 含 ../、绝对路径、盘符导致的落盘逃逸风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js 归档解压审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与归档条目名、解压目标目录、路径净化、符号链接条目和后续消费链相关的共享抓手
- 若项目存在 ArchiveService、PackageImporter、PluginInstaller、BackupRestore 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、静态目录、插件/模板目录与运行时控制面）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `unzipper.Extract` / `adm-zip` 的 `extractAllTo` / `extractEntryTo` / `yauzl` entry 流 / `extract-zip` / `tar-stream` entry 的调用点与目标目录来源
- `entryName` / `entry.fileName` / tar header `name` 是否包含 `../`、前导 `/` 绝对路径、盘符（`C:\`）与 UNC（`\\host\share`）片段
- `path.join(root, entryName)` 后是否做 `path.resolve` + 前缀校验，校验是否在规范化之前执行
- 符号链接 / 硬链接条目（tar symlink/hardlink）与目录型条目的覆盖行为
- 解压目标是否位于 `public/`、插件目录、模板目录、可下载目录等可达面
- 解压结果是否被动态 `require`、模板渲染、配置读取等后续链消费
- 上传归档 → 暂存 → 解压 → 落盘 → 消费的完整链路（上传过滤与 limits 归 node-file-upload-audit）

## 枚举规则（强制细化）

- 枚举所有 `unzipper`、`Extract({ path`、`adm-zip`、`extractAllTo(`、`extractEntryTo(`、`yauzl`、`extract-zip`、`tar-stream`、`decompress(`、`entry(` 调用点
- 优先搜索 extract、unzip、untar、archive、restore、import、theme、plugin、backup 等业务语义
- 对每个解压点记录：归档来源、目标目录、`entryName` 处理方式、最终解析路径、解压后可达面
- 区分库内置防护与项目自建净化，确认实际生效版本（核对 `package-lock.json` / `node_modules` 与已知 Zip Slip 修复记录）
- 检查条目名净化是否仅为字符串替换 `../`（可被 `....//`、编码变体绕过），而非 resolve 后校验
- 检查 zip / tar 符号链接条目是否被拒绝，或创建后是否做最终路径校验
- 若存在二次封装，必须逐层展开到真实解压库调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 条目路径净化 | 过滤 `../`、前导 `/`、盘符、空字节 | 检查净化是否在 `path.join` 前逐条目执行、是否覆盖 `....//` 与编码变体 | 规范化后逐条目校验 → ✅ 安全；仅字符串替换原始 `../` → ⚠️ 可绕过；无净化 → 🔴 高危 |
| 目标根前缀校验 | `path.resolve(root, entryName)` + `startsWith(root + path.sep)` | 检查校验是否在 resolve 之后执行且包含路径分隔符 | resolve 后锁定且 fail-close → ✅ 安全；缺少分隔符（`/app-evil` 冒充 `/app`）→ ⚠️ 可绕过；直接 `path.join` 落盘 → 🔴 高危 |
| 条目类型限制 | 拒绝 symlink/hardlink/设备条目 | 检查解压库对条目类型的处理与项目侧过滤 | 非普通文件条目拒绝 → ✅ 安全；symlink 条目直接创建 → 🔴 高危；行为依赖库版本 → ⚠️ 待确认 |
| 目标目录隔离 | 解压到非 Web 可达目录 | 核对解压根与 `public/`、插件、模板、配置目录关系 | 非 Web 目录且无消费链 → ✅ 安全；落入可达面 → 🔴 高危 |
| 覆盖策略 | 冲突拒绝 / 重命名 / 白名单内覆盖 | 检查同名条目覆盖逻辑是否可替换既有配置或脚本 | 冲突拒绝或重命名 → ✅ 安全；静默覆盖任意已有文件 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控归档条目疑似未经净化进入解压落盘路径
- `待确认`：上下文显示可疑模式，但外部输入来源、barrier 行为或调用链不清晰
- `误报`：输入来自固定常量 / 枚举映射，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到外部可控输入进入 Sink 位的证据 → `确认漏洞`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_ARCHIVE_EXTRACT_POINT` + `EVID_NODE_ARCHIVE_ENTRY_PATH_SANITIZE` 缺失：`entryName` 直通 `path.join` 落盘
- `EVID_NODE_ARCHIVE_EXTRACT_POINT` + `EVID_NODE_ARCHIVE_ZIP_SLIP_GUARD` 校验可绕过：绝对路径、盘符或 `....//` 变体逃逸基目录
- 解压落点位于 `public/`、插件或模板目录，且条目可覆盖既有配置 / 脚本

### ⚠️待验证

- 解压点存在，但归档来源（用户上传 / 远程拉取）不清晰（需补 trace 或调用链）
- 净化或前缀校验函数存在，但当前条目分支是否调用无法确认
- 符号链接条目行为依赖解压库版本，锁文件版本与实际安装版本不一致

### 误报

- 每个条目均经 `path.resolve` 后前缀校验且 fail-close，越界条目明确拒绝
- 解压库内置防护已确认生效（锁定版本无已知 Zip Slip）+ 项目侧二次校验
- 归档内容由服务端固定生成，条目名不包含外部输入

## 测试建议（强制）

### 正向测试

- 构造含 `../../../.ssh/authorized_keys`、绝对路径 `/etc/cron.d/pwn`、盘符 `C:\Temp\evil` 条目的 zip/tar 包
- 构造 `....//....//` 与双重编码变体条目、tar 符号链接条目，验证逃逸与链接跟随
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造正常条目归档，验证解压成功且文件落在目标根内
- 构造越界条目，验证前缀校验明确拒绝并中断解压流程
- 验证 symlink 条目在类型限制下被拒绝

### 回归测试

- 修复后复测，确认前缀校验对全部逃逸变体仍然生效
- 升级解压库版本后复测，确认内置防护与项目校验叠加有效
- 在 Windows / Linux 双平台验证盘符、反斜杠与路径分隔符差异

## 证据引用

- `EVID_NODE_ARCHIVE_EXTRACT_POINT`
- `EVID_NODE_ARCHIVE_ENTRY_PATH_SANITIZE`
- `EVID_NODE_ARCHIVE_ZIP_SLIP_GUARD`

## 输出

- `node/vuln_audit/archive-extract_{timestamp}.md`
- `node/vuln_poc/archive-extract_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
