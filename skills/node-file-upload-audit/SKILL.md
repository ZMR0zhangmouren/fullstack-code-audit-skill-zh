---
name: node-file-upload-audit
description: Node.js 文件上传审计工具。识别 multer/busboy/formidable 文件名未净化、落盘目录可控、fileFilter/limits 缺失等风险，输出分级、证据与修复建议。
---

# Node.js 文件上传审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与文件上传、文件名解析、落盘路径、文件过滤限制相关的共享抓手
- 若项目存在 UploaderService、FileStorage、AttachmentHelper 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、序列化配置、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **静态证据驱动**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- multer/busboy/formidable 的 `filename` 未净化（`../` 穿越）
- `dest`/`uploadDir` 可控导致落盘目录逃逸
- `fileFilter`/`limits` 缺失或配置宽松
- 可执行后缀（`.php`、`.jsp`、`.js`、`.sh`、`.exe` 等）落入静态可访问目录
- 原始文件名未经重命名直接回显或被前端二次引用

## 枚举规则（强制细化）

- 枚举所有 `multer(`、`busboy`、`formidable`、`diskStorage`、`filename:`、`dest:`、`uploadDir`、`fileFilter`、`limits` 调用点与配置对象
- 对每个上传接收点记录：中间件类型、落盘目录、文件名生成策略、fileFilter 白名单、limits 尺寸/数量限制、静态目录映射关系
- 区分直接落盘（`dest`/`uploadDir`）与自定义 storage（`diskStorage({ destination, filename })`）
- 检查 `filename` 回调是否直接使用 `file.originalname` 或未清洗的外部输入
- 检查 `dest`/`destination` 是否拼接用户可控路径或相对路径
- 检查 `fileFilter` 是否存在、扩展名/MIME 校验策略、是否为 fail-close（白名单模式）
- 检查 `limits.fileSize`、`limits.files` 等是否配置并能有效拦截超限请求
- 检查落盘目录是否位于 Web 根目录（如 `public/`、`static/`、`uploads/`）且可被直接请求执行
- 若存在二次封装，必须逐层展开到真实 multer/busboy/formidable 配置点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 文件名重生成 | 随机名 + 白名单后缀（UUID / 哈希 + `.ext`） | 检查 `filename` 回调是否丢弃原始名并使用安全随机名 | 随机名且扩展名白名单 → ✅ 安全；原始名直接落盘或扩展名黑名单 → 🔴 高危 |
| fileFilter 白名单 | 扩展名白名单 / MIME 类型校验 | 读取 fileFilter 源码，确认是否为 fail-close（未知类型拒绝） | fail-close（白名单） → ✅ 安全；黑名单 / MIME 单一校验 → ⚠️ 可绕过；无 fileFilter → 🔴 高危 |
| limits 尺寸/数量限制 | `limits.fileSize`、`limits.files`、`limits.fields` | 检查 limits 配置与后端校验是否一致 | 配置合理且后端强制生效 → ✅ 安全；配置缺失或仅前端校验 → ⚠️ 待确认 |
| 落盘目录与 Web 根隔离 | 写入非 Web 可访问目录；静态目录不解析脚本 | 检查 `dest`/`uploadDir`/`destination` 与 Web 根关系 | 非 Web 目录或静态目录禁止脚本执行 → ✅ 安全；可执行后缀落入 Web 可访问目录 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入文件名、落盘路径或文件过滤配置
- `待确认`：上下文显示可疑模式，但外部输入来源、barrier 行为或调用链不清晰
- `误报`：输入来自固定常量/枚举映射，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到外部可控输入进入 Sink 位的证据 → `确认漏洞`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知/非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG` + `EVID_NODE_UPLOAD_FILENAME_SANITIZE` + 无有效 Barrier
- 外部可控参数直接进入 `filename`/`dest`/`uploadDir` 且未做路径规范化或随机重命名
- 可执行后缀文件落入 Web 可访问目录，且可被直接请求执行
- `fileFilter` 为黑名单模式或 MIME 单一校验，可被双扩展名、截断、空字节等方式绕过

### ⚠️待验证

- 上下文显示可疑模式（如 `multer({ dest: req.query.dir })`），但外部输入来源不清晰（需补 trace 或调用链）
- Barrier 函数（如文件名随机化、扩展名白名单）存在，但当前分支是否调用、返回值是否被使用无法确认
- 落盘目录与 Web 根关系依赖运行时配置（如 `process.env.UPLOAD_DIR`），静态无法确认隔离性

### 误报

- 文件名完全由服务器生成随机名，扩展名来自固定白名单
- 落盘目录为非 Web 可访问目录，且静态目录不解析脚本
- `fileFilter` 为 fail-close 白名单，未知扩展名明确拒绝
- 上传文件仅供下载流式读取，不进入任何执行/渲染上下文

## 测试建议（强制）

### 正向测试

- 构造文件名包含 `../` / `..\` / 空字节 / 双扩展名（`.jpg.php`）的上传请求
- 构造超出 `limits.fileSize` / `limits.files` 的上传请求
- 构造可执行脚本后缀文件上传至 Web 可访问目录并尝试直接请求
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造白名单扩展名文件，验证正常落盘
- 构造非法扩展名 / 超大文件，验证被 barrier 明确拒绝
- 验证随机重命名后原始文件名不再参与路径解析或回显

### 回归测试

- 修复后复测，确认 fileFilter 白名单、文件名重生成、落盘目录隔离仍然生效
- 复测 `limits` 超限拒绝逻辑，确认未引入 bypass
- 验证新增文件类型加入白名单时仍保持 fail-close

## 证据引用

- `EVID_NODE_UPLOAD_MIDDLEWARE_CONFIG`
- `EVID_NODE_UPLOAD_FILENAME_SANITIZE`
- `EVID_NODE_UPLOAD_FILTER_LIMITS`
- `EVID_NODE_UPLOAD_ACCESSIBILITY`

## 输出

- `node/vuln_audit/file-upload_{timestamp}.md`
- `node/vuln_poc/file-upload_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
