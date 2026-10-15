---
name: node-codegraph-indexer
description: Node.js 项目 CodeGraph 索引管理工具。检测目标项目 CodeGraph 环境、建立/刷新代码知识图索引，产出索引本体、状态与元数据文件，供 node-route-mapper 与 node-route-tracer 调用链加速使用。
---

# Node.js CodeGraph 索引管理

## 目标

对目标 Node.js 项目建立或刷新 CodeGraph 本地代码知识图索引（`.codegraph/`），使后续 `node-route-mapper` 与 `node-route-tracer` 能通过 `codegraph_explore` / `codegraph_callers` / `codegraph_impact` 获取跨文件调用链（入口定义、中间件链、require/import 依赖关系），替代部分手动的 grep + Read 组合。

## CRITICAL：索引不是审计替代

- CodeGraph 是**执行层加速工具**，不是审计规则本身
- 路由识别、参数绑定、Sink 判定、证据闭合仍由现有 Skill 负责
- 无 CodeGraph 索引时，100% 回退现有静态分析流程（与 dotnet 侧阶段 0 语义一致）

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引；本 Skill 的检索关键字（入口定义 / 绑定与参数 / 前置控制 / 敏感操作 / 安全配置 五层）与该索引对齐，用于确认索引覆盖面而非直接枚举漏洞
- 本 Skill 不直接审计漏洞，因此不引用 `shared/EVIDENCE_POINT_IDS.md` 中的 Sink 证据点；Sink 证据契约由各 `node-vuln-audit` 专项按各自 EVID_NODE_* 引用
- **默认遵循 `shared/AUDIT_EXECUTION_COMMON.md`（栈无关执行标准真源，shared 演进决策 3）与 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范（`node/codegraph/*`、`node/quality/*`）
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范（本 Skill 涉及索引可用性分级，不产生漏洞级结论）

## 输入依赖

- 必需：`node_source_path`（Node.js 项目或仓库根目录，应包含 `package.json`）
- 可选：`package.json`（读取 `dependencies` / `devDependencies`，用于技术栈判定与索引覆盖范围确认；排除 `node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`、`coverage` 等非审计目录）
- 可选：技术栈检出结果（`node/stack_detect/stack_detect_{timestamp}.md`，由 `node-audit-pipeline` 阶段 0 或 `node-route-mapper` 侦察产出；如已存在，用于对齐框架面与入口类型，缩小索引符号核对范围）
- 本 Skill 位于 pipeline 阶段 0，先于 route-mapper / route-tracer 执行；无其他上游强制依赖

## 重点检查

- CodeGraph 环境可用性：`codegraph` CLI 是否在 PATH、`node_source_path` 下是否已存在 `.codegraph/`
- JS/TS 符号提取完整性：`codegraph query --kind function` / `--kind class` 能否命中源码符号
- 入口与中间件符号可检索：按框架面（Express / NestJS / Next.js / Koa / Fastify / Nuxt）确认路由级符号可被检索
- 依赖关系边：`require` / `import` 跨文件引用是否进入索引（供 route-tracer 跨文件追链）
- 关键文件覆盖：磁盘 `.js` / `.ts` / `.jsx` / `.tsx` 文件数与索引中文件数对比，记录覆盖率
- 降级记录：索引不可用时必须落盘 `UNAVAILABLE` 状态与原因，禁止假装索引可用

## 枚举规则（强制细化）

### 1. 入口与中间件符号

- 检索关键字：`codegraph query --kind function --limit 5` 等 CodeGraph 查询，叠加 `shared/NODE_AUDIT_GRABBER_INDEX.md` 入口定义抓手关键字（`app.get` / `Router()` / `@Controller` / `@Get` / `export function GET` / `defineEventHandler` / `fastify.route` 等）
- 记录要求：入口符号名、路由模板、HTTP 方法、中间件链符号（`app.use` / `router.use` / `@UseGuards` / `addHook` 等），逐条写入 `node/codegraph/codegraph_index_{timestamp}.md`

### 2. 依赖关系边

- 检索方式：`codegraph_callers {symbol}` / `codegraph_explore "module imports of {file}"`（或等效查询）
- 记录要求：模块级依赖、文件间引用边、项目内二次封装链；CodeGraph 独有跨文件边标注 `source: codegraph`

### 3. 索引覆盖与质量

- 对比磁盘 JS/TS 文件数与索引文件数，记录 `coverage_percent`
- 记录要求：缺失目录清单、符号缺失类型（如仅提取到函数未提取到类）、路由符号计数，全部写入 `node/quality/codegraph_index_validation_{timestamp}.md`

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| codegraph CLI 可用性 | `codegraph` 命令在 PATH | 执行 `codegraph --version` | 有版本输出 → 通过；命令不存在 → 降级 `UNAVAILABLE(NOT_AVAILABLE)` |
| `.codegraph/` 存在性 | 目标目录下 `.codegraph/` 目录 | 检查 `codegraph.db` 是否存在且非空 | 存在且非空 → 通过；缺失 → 进入 init 场景或降级 |
| JS/TS 符号提取 | `codegraph query --kind function` | 抽样查询 5 个符号 | ≥1 命中 → 通过；全空 → `PARTIAL` 并检查源码目录是否存在 |
| 路由级符号检索 | `codegraph explore` 路由查询 | 按检出框架面检索路由/中间件符号 | 命中 → 通过；0 命中且项目确为服务端项目 → `PARTIAL`；非服务端项目 → `NOT_APPLICABLE` |
| 文件覆盖率 | 磁盘文件数 vs 索引文件数 | 计数对比 | 记录 `coverage_percent`，注明排除目录；显著偏低（如 <50%）→ `PARTIAL` 并附原因 |

## 二阶段判定（强制）

本 Skill 遵循 `shared/AUDIT_EXECUTION_COMMON.md`（栈无关真源）与 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程。由于本 Skill 为**索引管理类**，二阶段判定应用于「索引可用性结论」而非漏洞结论：

### 阶段一：临时结论

对每条检测项先给出三选一临时结论：

- `确认可用`：CLI 可用且索引符号可检索
- `待确认`：CLI 可用但 `.codegraph/` 缺失或符号为空，需继续尝试 init / sync
- `不可用`：CLI 缺失或 init / sync 失败

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下执行至少一步（init 或 sync）并复检，直到满足以下任一条件：

- ✅ 找到索引建立成功且符号可检索的证据 → `AVAILABLE`
- ✅ 找到明确失败原因（CLI 缺失 / init 报错 / 项目非服务端）→ `UNAVAILABLE`，必须落盘原因
- ❌ 仍缺少关键步骤 → 保持 `UNAVAILABLE(PARTIAL)`，但必须说明缺失哪一步

**fail-close 语义**：索引不可用时下游 Skill 必须 100% 回退静态分析；任何「假装索引可用 / 以空索引结果代替审计面」的 silent-fallback 均视为错误。降级不得阻断 pipeline，但状态与原因必须落盘。

## 判定规则（强制细化）

### 已确认（AVAILABLE）

- `codegraph` CLI 可用，且 `.codegraph/` 索引存在并成功 init / sync
- JS/TS 符号与路由级符号可检索（`route_symbols_found > 0`，服务端项目）
- 文件覆盖率已记录，`codegraph_index_status` 与 `codegraph_index_validation` 两文件计数对账一致

### 待确认（PARTIAL）

- 索引存在但部分符号缺失（如仅函数、无类/无路由符号），或覆盖率显著偏低（<50%）
- 标记 `codegraph_status: UNAVAILABLE(PARTIAL)` 并说明缺失面；下游可部分使用但关键链路仍走静态分析

### 误报 / 不可用（UNAVAILABLE）

- `NOT_AVAILABLE`：CLI 未安装（附安装指引，不影响后续流程）
- `INIT_FAILED` / `SYNC_FAILED`：init / sync 执行失败（附错误日志摘要）
- `NOT_APPLICABLE`：项目确非 Node.js 服务端项目（如纯 SPA，参见 `NODE_AUDIT_GRABBER_INDEX.md` 排除规则）
- 必须记录原因；下游 Skill 完全回退静态分析

## 测试建议（强制）

### 正向测试

- 目标目录已有 `.codegraph/` 且 CLI 可用：执行 sync 成功，输出 `codegraph_status: AVAILABLE`，符号可检索
- 目标目录无 `.codegraph/` 但 CLI 可用：执行 init 成功，输出 `AVAILABLE`，`coverage_percent` 与磁盘对比合理

### 负向测试

- CLI 缺失：输出 `UNAVAILABLE(NOT_AVAILABLE)` + 安装指引，pipeline 不阻断，下游走静态分析
- init / sync 失败：输出 `UNAVAILABLE(INIT_FAILED/SYNC_FAILED)` + 错误摘要
- 符号提取为空但磁盘存在源码：输出 `UNAVAILABLE(PARTIAL)`，禁止以空索引冒充审计完成

### 回归测试

- P1 无 CodeGraph 环境时，pipeline 阶段 0 照常输出 `node/codegraph/codegraph_index_status_{timestamp}.md`（`codegraph_status: NOT_RUN` + 原因），与 `node-audit-pipeline` 阶段 0 现有语义一致
- 交付本 Skill 后，P1 执行流程不因新增 ACTIVE 状态而改变既有静态分析路径

## 证据引用

- 本 Skill 为索引管理类，不直接审计漏洞，因此**不引用** `shared/EVIDENCE_POINT_IDS.md` 中的 Sink 证据点（含 EVID_NODE_*）；Sink 证据契约由各 `node-vuln-audit` 专项负责
- 证据契约按索引产物自检：`node/codegraph/codegraph_index_{timestamp}.md`（索引本体）与 `node/codegraph/codegraph_index_status_{timestamp}.md`（状态元数据）、`node/quality/codegraph_index_validation_{timestamp}.md`（质量校验）三件套互相对账——状态文件中的符号计数 / 覆盖率必须可回溯到质量校验文件的统计，对账失败按 `shared/AUDIT_EXECUTION_COMMON.md` fail-close 语义处理

## 输出

- `node/codegraph/codegraph_index_{timestamp}.md`：索引本体快照（入口符号、中间件链、依赖关系边，供 route-mapper / route-tracer 加速）
- `node/codegraph/codegraph_index_status_{timestamp}.md`：索引状态与元数据（`codegraph_status: AVAILABLE|UNAVAILABLE` 及子状态）
- `node/quality/codegraph_index_validation_{timestamp}.md`：索引质量校验结果（符号提取、路由符号、文件覆盖率）

### 状态文件字段模板（`node/codegraph/codegraph_index_status_{timestamp}.md`）

```md
# CodeGraph Index Status (node)

- node_source_path: {node_source_path}
- timestamp: {timestamp}
- codegraph_status: {AVAILABLE|UNAVAILABLE}
- unavailable_reason: {N/A|NOT_AVAILABLE|INIT_FAILED|SYNC_FAILED|PARTIAL|NOT_APPLICABLE}
- cli_version: {version or N/A}
- index_exists: {true|false}
- init_or_sync: {init|sync|none}
- js_ts_file_count_on_disk: {n}
- file_count_in_index: {n}
- coverage_percent: {n}%
- route_symbols_found: {n}
- middleware_symbols_found: {n}
- framework_detected: {express|nestjs|nextjs|koa|fastify|nuxt|none|N/A}
- notes: {any warnings or failures}
```

## 核心输入

用户提供：

- `node_source_path`：Node.js 项目或仓库根目录（同「输入依赖」必需项）
- 可选：`package.json` 与技术栈检出结果（用于索引范围确认与符号核对）

## 执行步骤

### 步骤 1：检测 CodeGraph 环境

1. 检查目标目录 `node_source_path` 下是否已存在 `.codegraph/` 目录
   - 若存在：读取 `.codegraph/codegraph.db` 文件修改时间，记录 `index_exists: true`
   - 若不存在：记录 `index_exists: false`
2. 检测系统 PATH 中是否存在 `codegraph` 命令
   - 若存在：记录 `cli_available: true`，并获取版本号
   - 若不存在：记录 `cli_available: false`

### 步骤 2：索引建立或刷新

#### 场景 A：已存在 `.codegraph/` 且 CLI 可用

- 执行 `codegraph sync {node_source_path}` 进行增量更新
- 记录 `sync_status` 与更新时间戳

#### 场景 B：无 `.codegraph/` 但 CLI 可用

- 执行 `codegraph init {node_source_path}` 建立完整索引
- 记录 `init_status` 与耗时

#### 场景 C：CLI 不可用

- 在 `codegraph_index_status_{timestamp}.md` 中记录 `codegraph_status: UNAVAILABLE`、`unavailable_reason: NOT_AVAILABLE`
- 给出安装指引（不影响后续流程，后续 Skill 回退到现有静态分析）

### 步骤 3：索引质量校验

无论索引是否新建，执行以下校验（结果写入 `node/quality/codegraph_index_validation_{timestamp}.md`）：

1. **文件覆盖校验**：检查 `.codegraph/` 下 `codegraph.db` 是否存在且非空
2. **JS/TS 符号提取校验**：通过 `codegraph query --kind function --limit 5`（或等效方式）确认函数/类符号已提取
3. **路由识别校验**：按 `framework_detected` 面通过 `codegraph explore "express routes in {node_source_path}"`（或等效查询）确认路由级符号可被检索
4. **关键文件覆盖**：确认 `node_source_path` 下 `.js` / `.ts` / `.jsx` / `.tsx` 文件数量与索引中文件数量对比，记录覆盖率（默认排除 `node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`、`coverage`）

### 步骤 4：索引本体与元数据记录

1. 将入口符号、中间件链符号、依赖关系边写入 `node/codegraph/codegraph_index_{timestamp}.md`
2. 将索引状态与元数据写入 `node/codegraph/codegraph_index_status_{timestamp}.md`（字段见「状态文件字段模板」）

## 对下游 Skill 的消费约定

### node-route-mapper 消费方式

- 若 `codegraph_status = AVAILABLE` 且 `route_symbols_found > 0`：
  - 优先通过 `codegraph explore "{framework} routes in {node_source_path}"` 获取入口/路由映射
  - 通过 `codegraph query --kind function` 补充 handler 函数列表
  - 将 CodeGraph 返回的路由符号与手动静态分析结果交叉验证，差异项标记 `⚠️需人工复核`
- 若 `codegraph_status != AVAILABLE`：完全回退现有静态分析流程

### node-route-tracer 消费方式

- 若 `codegraph_status = AVAILABLE`：
  - 对每条 `route_id`，优先通过 `codegraph_callers {handler_symbol}` 获取调用链上游
  - 通过 `codegraph_impact {handler_symbol} --depth 3` 获取影响半径（含跨文件调用）
  - 对中间件链路，通过 `codegraph_explore "middleware chain of {app_symbol}"` 定位中间件挂载顺序
  - 将 CodeGraph 调用链与手动 trace 结果合并，CodeGraph 独有的跨文件边标注 `source: codegraph`
- 若 `codegraph_status != AVAILABLE`：完全回退现有 trace 流程

## 检查点设计

- 🔴 **CHECKPOINT A（环境检测）**：确认 `codegraph` CLI 可用性与 `.codegraph/` 存在性
- 🔴 **CHECKPOINT B（索引质量）**：确认 JS/TS 符号已提取、路由级符号可检索
- 🟡 **CHECKPOINT C（降级确认）**：若索引不可用，确认下游 Skill 已知晓并回退静态分析

## 失败与降级分支

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| `codegraph` CLI 未安装 | 输出安装指引，标记 `UNAVAILABLE(NOT_AVAILABLE)` | 不影响后续流程，下游 Skill 走静态分析 |
| `codegraph init` 失败 | 记录错误日志，标记 `UNAVAILABLE(INIT_FAILED)` | 下游 Skill 走静态分析 |
| JS/TS 符号提取为空 | 检查源码文件是否存在，若存在则标记 `UNAVAILABLE(PARTIAL)` | 下游 Skill 走静态分析 |
| 路由符号识别为 0 | 确认项目是否真为 Node.js 服务端项目；若不是则标记 `NOT_APPLICABLE` | 若是服务端项目但识别为 0，标记 `UNAVAILABLE(PARTIAL)` |

## 不要做的事

- 反模式：因 CodeGraph 索引失败而阻断整个 pipeline。正确做法：标记状态并回退。
- 反模式：用 CodeGraph 结果替代 route-mapper 的完整输出。正确做法：仅作为加速输入，最终 routes/params 仍由 route-mapper 统一格式化输出。
- 反模式：在索引阶段做 Sink 判定或漏洞分析。正确做法：仅建立索引，审计留给后续 Skill。
- 反模式：索引覆盖率统计把 `node_modules/` 计入审计面。正确做法：默认排除 `node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`、`coverage`（lockfile 例外归供应链审计）。
