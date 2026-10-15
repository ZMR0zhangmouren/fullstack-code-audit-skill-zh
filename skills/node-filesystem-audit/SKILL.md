---
name: node-filesystem-audit
description: Node.js 文件系统操作综合审计工具。识别 fs.rename/unlink/chmod/access 全族操作中 path.join/resolve 用户输入参与、symlink 跟随与目录权限范围风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js 文件系统操作审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与路径输入收敛、链接跟随、TOCTOU、目录权限和删除/移动/复制相关的共享抓手
- 若项目存在 StorageManager、PathHelper、CleanupJob、SyncService 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于关联触发入口、路径来源与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于关联后台清理任务、管理入口与权限边界）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、容器挂载与运行时控制面）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **静态证据驱动**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `fs.rename` / `unlink` / `chmod` / `chown` / `access` / `mkdir` / `rm` / `cp` / `mkdtemp` 等综合操作面的路径来源
- `path.join` / `path.resolve` 中用户输入参与位置：固定根 + 可控子段还是整段可控
- 符号链接跟随：`fs.stat`（跟随）与 `fs.lstat`（不跟随）的选择，`fs.realpath` 解析时机
- 检查与使用分离导致的 TOCTOU：`fs.access` → `fs.writeFile`、先校验后 rename 的时间窗
- 运行时权限范围：`chmod 0o777`、`process.umask(0)`、容器挂载目录与非 root 运行账户
- 删除 / 覆盖 / 清理逻辑作为链式利用前置条件：删除锁文件、替换配置、覆盖计划任务输入
- **专项边界**：单点读取、写入、归档解压分别归 node-file-read-audit / node-file-write-audit / node-archive-extract-audit；本专项管综合操作面、链接行为与权限范围

## 枚举规则（强制细化）

- 枚举所有 `rename(`、`unlink(`、`chmod(`、`chown(`、`access(`、`mkdir(`、`rm(`、`cp(`、`mkdtemp(`、`realpath(`、`symlink(`、`lstat(`、`stat(` 调用点
- 优先搜索 temp、cache、upload、export、log、backup、staging、working、quarantine 等目录语义
- 对每个操作点记录：触发入口、路径来源、`stat`/`lstat` 选择、竞态窗口、权限边界
- 检查 `path.join` 第二参数起是否直接拼接 `req.params` / `req.query` / `req.body` 来源
- 检查 `chmod` 权限位是否过宽、`process.umask` 是否被置 0、操作目录是否暴露在容器挂载卷
- 检查同一路径在多步骤流程中是否先校验后重建（拼接点漂移导致校验失效）
- 若存在二次封装，必须逐层展开到真实 `fs` 调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 路径输入收敛 | 固定根 + 文件名 allowlist | 检查 `path.join` 各参数来源与 allowlist 实现 | 仅文件名可控且 allowlist fail-close → ✅ 安全；目录段可控 → ⚠️ 待确认；整段路径可控 → 🔴 高危 |
| 符号链接校验 | `fs.lstat` + `isSymbolicLink()` 拒绝 | 检查操作前是否用 `lstat` 而非 `stat` 校验目标 | `lstat` 拒绝链接 → ✅ 安全；仅 `stat`（跟随链接）→ ⚠️ 可绕过；无校验 → 🔴 高危 |
| TOCTOU 防护 | 原子操作（`rename`）/ 打开后 `fstat` | 检查校验点与操作点之间是否存在可注入时间窗 | 校验与操作原子化 → ✅ 安全；`access` 后再写存在窗口 → ⚠️ 待确认 |
| 权限范围最小化 | `chmod` 最小权限、目录隔离、非 root 运行 | 核对权限位、运行账户与容器挂载边界 | 最小权限且目录隔离 → ✅ 安全；`0o777` 或 root 运行 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似参与文件系统综合操作路径或权限调整
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

- `EVID_NODE_FS_OPERATION_POINT` + `EVID_NODE_FS_PATH_JOIN_CONTROL` + 无有效 Barrier：用户输入参与 `path.join` 后直达 rename/unlink/chmod
- `EVID_NODE_FS_OPERATION_POINT` + `EVID_NODE_FS_SYMLINK_FOLLOW`：操作前仅用 `fs.stat` 校验，符号链接可重定向到敏感路径
- `EVID_NODE_FS_PERMISSION_SCOPE` 佐证影响面：`chmod 0o777`、容器挂载目录可写或 root 运行放大操作后果

### ⚠️待验证

- 操作点存在，但路径来源（固定目录段或请求参数）不清晰（需补调用链）
- `lstat` 符号链接校验存在，但当前分支是否调用、失败时是否拒绝无法确认
- 权限边界依赖运行时环境（容器挂载、umask、服务账户），静态无法确认

### 误报

- 路径来自固定常量 / 枚举映射，未知输入明确拒绝（fail-close）
- `fs.lstat` + `isSymbolicLink()` 拒绝链接，且操作为原子 rename
- 用户输入不参与路径，目录权限最小化且运行账户受限

## 测试建议（强制）

### 正向测试

- 构造符号链接指向 `/etc/passwd` 后触发 `unlink` / `chmod` 的请求，验证链接跟随
- 构造 `..` 参与 `path.join` 的目录段输入与 TOCTOU 竞态（校验后替换目标）
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造含符号链接的目标，验证 `lstat` 校验明确拒绝
- 构造越界路径与非法权限调整，验证被拒绝且无部分执行
- 验证 allowlist 外文件名被拒绝

### 回归测试

- 修复后复测，确认链接校验与路径收敛仍然生效
- 在 Windows / Linux 双平台复测 junction 与符号链接解析差异
- 验证新增清理 / 同步类任务时仍保持原子操作与最小权限

## 证据引用

- `EVID_NODE_FS_OPERATION_POINT`
- `EVID_NODE_FS_PATH_JOIN_CONTROL`
- `EVID_NODE_FS_SYMLINK_FOLLOW`
- `EVID_NODE_FS_PERMISSION_SCOPE`
- `EVID_NODE_CFG_RUNTIME_SETTING`（目录来源 / umask / 容器环境变量等运行时配置叠加证据）

## 输出

- `node/vuln_audit/filesystem_{timestamp}.md`
- `node/vuln_poc/filesystem_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
