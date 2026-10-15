---
name: node-file-read-audit
description: Node.js 文件读取与路径穿越审计工具。识别 fs.readFile/readFileSync/createReadStream、res.sendFile/res.download 与 express.static 挂载范围中的路径拼接、双编码与目录逃逸风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js 文件读取审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与读取路径构造、规范化、基目录锁定、下载接口和静态目录挂载相关的共享抓手
- 若项目存在 FileService、AttachmentReader、DownloadController、StaticResolver 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐读取/下载入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与静态中间件挂载位置）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、静态目录挂载与运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `fs.readFile` / `readFileSync` / `createReadStream` / `fs.promises.readFile` 读取点的路径来源
- `res.sendFile` / `res.download` 下载与附件接口的 path 参数可控性，以及 `sendFile` 的 `root` 选项是否启用
- `express.static` / `serve-static` / `koa-static` 挂载根目录、`dotfiles` 与 `fallthrough` 配置
- `path.join(req.params.xxx)` / `path.join(req.query.xxx)` 目录穿越与 `path.resolve` 后前缀校验缺失或先校验后拼接
- `decodeURIComponent` 解码顺序与双编码（`%252e%252e%252f`）绕过
- 读取目标是否覆盖 `.env`、密钥、配置、源码、日志、上传文件等敏感资产
- 读取内容是否进一步进入模板渲染、配置解析、动态 `require` 等执行边界

## 枚举规则（强制细化）

- 枚举所有 `readFile(`、`readFileSync(`、`createReadStream(`、`fs.promises.readFile`、`sendFile(`、`download(`、`express.static(`、`serve-static`、`koa-static` 调用点
- 优先搜索 path、file、filename、template、view、config、download、export、doc、attachment 等参数名
- 对每个读取点记录：目标根目录、`path.join`/`path.resolve` 拼接逻辑、前缀校验位置、编码处理、输出方式、鉴权条件
- 区分整段路径可控、目录段可控与仅文件名可控三种模式
- 检查静态中间件挂载根是否覆盖 `.env`、源码、日志等敏感目录，`dotfiles` 配置是否允许 `/.env` 类请求
- 检查 `res.sendFile` 是否传入 `root` 选项：未传 `root` 时请求中的绝对路径可直接命中
- 若存在二次封装，必须逐层展开到真实 `fs` / `send` 库调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 路径规范化与基目录锁定 | `path.resolve` + `startsWith(root + path.sep)` 前缀校验 | 检查校验是否在规范化之后执行、前缀比较是否包含路径分隔符 | 规范化后锁定且 fail-close → ✅ 安全；先校验后拼接或缺少分隔符（`/app-evil` 冒充 `/app`）→ ⚠️ 可绕过；无基目录锁定 → 🔴 高危 |
| 路径遍历过滤 | `decodeURIComponent` 后过滤 `../`、`..\`、空字节 | 检查过滤是否在解码之后执行且覆盖编码与重复编码变体 | 解码后过滤且覆盖全部变体 → ✅ 安全；仅字符串替换原始 `../` → ⚠️ 可绕过；无过滤 → 🔴 高危 |
| 扩展名/文件类型白名单 | 扩展名 allowlist + MIME 校验 | 读取白名单实现源码，确认未知类型是否拒绝 | fail-close（白名单外拒绝）→ ✅ 安全；黑名单模式 → ⚠️ 可绕过；无限制 → 🔴 高危 |
| 静态目录边界 | `express.static` 挂载根选择、`dotfiles: 'deny'`、`fallthrough: false` | 核对挂载根与敏感目录关系及 dotfiles/fallthrough 配置 | 挂载根隔离敏感目录且 dotfiles 拒绝 → ✅ 安全；挂载根包含 `.env`/源码目录 → 🔴 高危 |
| 鉴权与资源归属 | 中间件鉴权 + 资源归属校验（防 IDOR） | 检查读取前是否有身份校验与资源归属校验 | 身份+归属双校验 → ✅ 安全；仅身份无归属 → ⚠️ 待确认；无鉴权 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入读取路径构造或静态目录暴露面
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

- `EVID_NODE_FILE_READ_POINT` + `EVID_NODE_FILE_READ_PATH_CONSTRUCTION` + 无有效 `EVID_NODE_FILE_READ_TRAVERSAL_GUARD`
- 用户可控参数经 `path.join` 拼接直达 `fs.readFile` / `res.sendFile`，且无 resolve 后前缀校验
- `express.static` / `serve-static` 挂载根覆盖 `.env`、源码或日志目录（`EVID_NODE_FILE_READ_STATIC_ROOT`）
- 前缀校验先于解码执行，可被双编码（`%252e%252e%252f`）或未传 `root` 的绝对路径直通绕过

### ⚠️待验证

- 上下文显示可疑模式（如 `fs.readFile(path.join(base, req.query.file))`），但外部输入来源不清晰（需补 trace 或调用链）
- 前缀校验函数存在，但当前分支是否调用、返回值是否被使用无法确认
- 静态目录挂载根依赖运行时配置（如 `process.env.STATIC_ROOT`），静态无法确认边界

### 误报

- 最终路径来自固定常量 / 枚举映射，未知路径会拒绝读取（fail-close）
- `path.resolve` 后前缀校验 fail-close，且有扩展名白名单与资源归属校验
- 用户输入仅影响文件名（无目录段），且文件名经过严格 allowlist 校验

## 测试建议（强制）

### 正向测试

- 构造路径穿越输入：`../../../etc/passwd`、`..%2f..%2fetc/passwd`、双编码 `%252e%252e%252f`、反斜杠 `..\..\windows\win.ini`
- 构造绝对路径直通（`path=/etc/passwd`）与 dotfile 请求（`/.env`）验证静态目录边界
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造被 barrier 拦截的输入：基目录外路径、白名单外扩展名、超长路径
- 验证 resolve 后前缀校验对编码变体与符号链接的拦截效果
- 验证 `dotfiles: 'deny'` 配置下 `/.env` 类请求被明确拒绝

### 回归测试

- 修复后复测，确认基目录锁定与前缀校验仍然生效
- 复测双编码、符号链接、大小写等变体，确认未引入新的绕过路径
- 验证新增挂载目录或下载接口时仍保持基目录锁定 fail-close

## 证据引用

- `EVID_NODE_FILE_READ_POINT`
- `EVID_NODE_FILE_READ_PATH_CONSTRUCTION`
- `EVID_NODE_FILE_READ_TRAVERSAL_GUARD`
- `EVID_NODE_FILE_READ_STATIC_ROOT`
- `EVID_NODE_CFG_SECURITY_SWITCH`（`dotfiles` / `fallthrough` / 挂载根等安全开关叠加证据）

## 输出

- `node/vuln_audit/file-read_{timestamp}.md`
- `node/vuln_poc/file-read_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
