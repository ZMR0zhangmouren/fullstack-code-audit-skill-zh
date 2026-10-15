---
name: node-file-write-audit
description: Node.js 任意文件写入审计工具。识别 fs.writeFile/writeFileSync/appendFile/createWriteStream 与 multer 落盘回调中路径与内容可控导致的敏感文件覆盖风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js 文件写入审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与路径拼接、文件名生成、覆盖模式、写入内容来源和写后消费链相关的共享抓手
- 若项目存在 FileStore、ConfigWriter、ExportService、ReportGenerator 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐写入入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、可访问目录与运行时控制面）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `fs.writeFile` / `writeFileSync` / `appendFile` / `createWriteStream` / `fs.promises.writeFile` 写入点
- `multer` 的 `diskStorage({ destination, filename })` 回调路径与文件名生成（上传过滤与 limits 归 node-file-upload-audit，本专项聚焦落盘路径与覆盖面）
- 用户输入如何进入目标路径、文件名、目录段或扩展名
- 写入内容来源：`req.body`、模板串、远程拉取内容、反序列化数据
- `flag` 配置：`'w'` 直接覆盖、`'ax'`/`'wx'` 冲突拒绝、追加模式对已有文件的污染
- 写入扩展名/落点可控时能否覆盖 `.env`、`package.json`、crontab、模板、`authorized_keys` 等敏感文件
- 写后消费链：静态资源、下载接口、动态 `require`、模板渲染、pm2 / 计划任务

## 枚举规则（强制细化）

- 枚举所有 `writeFile(`、`writeFileSync(`、`appendFile(`、`createWriteStream(`、`fs.promises.writeFile`、`outputFile(`、`move(`、`copy(` 调用点
- 优先搜索 dest、path、target、filename、output、export、report、template、config 等目标路径字段
- 对每个写入点记录：路径来源、内容来源、`flag` 配置、覆盖冲突策略、写后访问面
- 区分路径可控与内容可控两条独立证据链，双链均闭合才可下强结论
- 检查 `fs-extra` 的 `outputFile` / `move` / `copy` 等封装是否透传用户输入到真实 `fs` 调用
- 检查 multer 落盘回调中的文件名拼接与 `destination` 目录选择逻辑是否使用原始文件名或请求参数
- 若存在二次封装，必须逐层展开到真实 `fs` 调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 路径规范化与基目录锁定 | `path.resolve` + 前缀校验（含 `path.sep`） | 检查拼接、规范化、校验的先后顺序与分隔符处理 | 校验在 resolve 后且 fail-close → ✅ 安全；校验后重新拼接原始输入 → ⚠️ 可绕过；无基目录锁定 → 🔴 高危 |
| 文件名重生成/白名单 | 随机名（UUID/哈希）+ 固定扩展名 | 检查文件名是否丢弃原始输入、扩展名是否来自白名单 | 随机名 + 白名单 → ✅ 安全；原始名或扩展名直通落盘 → 🔴 高危 |
| 覆盖保护 | `flag: 'ax'` / `'wx'`、冲突拒绝策略 | 检查写入 flag 与已有文件冲突处理逻辑 | `'ax'`/`'wx'` 冲突即失败 → ✅ 安全；`'w'` 直写可控路径 → 🔴 高危；先 `access` 后写入（TOCTOU）→ ⚠️ 待确认 |
| 内容与扩展名控制 | 扩展名 allowlist、内容 schema 校验 | 检查写入内容是否校验、扩展名是否固定 | 内容校验 + 固定扩展名 → ✅ 安全；内容与扩展名均由请求决定 → 🔴 高危 |
| 写后可达隔离 | 非 Web 目录落盘、静态目录不解析脚本 | 核对落点与 Web 根、模板目录、插件目录关系 | 非 Web 目录且无消费链 → ✅ 安全；落入可执行/可渲染目录 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入写入路径构造或写入内容映射
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

- `EVID_NODE_FILE_WRITE_POINT` + `EVID_NODE_FILE_WRITE_PATH_CONSTRUCTION` + 无有效 `EVID_NODE_FILE_WRITE_OVERWRITE_PROTECTION`
- 用户可控路径可覆盖 `.env`、`package.json`、模板或 crontab 等敏感文件，且 `flag: 'w'` 直写
- 写入内容与扩展名均由请求决定（`EVID_NODE_FILE_WRITE_CONTENT_CONTROL`），落点可被静态资源、模板渲染或动态 `require` 消费
- 前缀校验存在但校验后重新拼接原始输入，可被编码变体或符号链接绕过

### ⚠️待验证

- 写入点存在，但路径来源与内容来源任一链条不清晰（需补 trace 或调用链）
- 覆盖保护（如 `'ax'` flag、冲突检查）存在，但当前分支是否调用、返回值是否被使用无法确认
- 写后可达性依赖运行时配置（如 `process.env.OUTPUT_DIR` 指向 Web 目录）

### 误报

- 路径与内容均来自固定常量 / 白名单，未知输入明确拒绝（fail-close）
- 目标文件名由服务端随机生成，`flag: 'ax'`/`'wx'` 冲突即失败
- 写后文件位于非 Web 目录，且无模板渲染 / 动态 `require` / 计划任务等消费链

## 测试建议（强制）

### 正向测试

- 构造 `../` 覆盖 `.env`、`package.json` 的写入请求，验证目标文件确实被替换
- 构造写入 `.js` 文件到静态可执行目录并请求触发，或写入模板文件后触发渲染
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造基目录外路径、白名单外扩展名，验证被明确拒绝
- 验证 `flag: 'ax'` 在目标已存在时写入失败且无部分写入残留
- 验证随机重命名后原始文件名不再参与落盘路径

### 回归测试

- 修复后复测，确认基目录锁定与覆盖保护仍然生效
- 复测临时文件 + `fs.rename` 原子替换链，确认未引入新的绕过路径
- 验证新增导出/报表功能时仍保持路径与内容双链校验

## 证据引用

- `EVID_NODE_FILE_WRITE_POINT`
- `EVID_NODE_FILE_WRITE_PATH_CONSTRUCTION`
- `EVID_NODE_FILE_WRITE_OVERWRITE_PROTECTION`
- `EVID_NODE_FILE_WRITE_CONTENT_CONTROL`
- `EVID_NODE_CFG_RUNTIME_SETTING`（落盘目录 / 输出路径来自 `process.env` 的叠加证据）

## 输出

- `node/vuln_audit/file-write_{timestamp}.md`
- `node/vuln_poc/file-write_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
