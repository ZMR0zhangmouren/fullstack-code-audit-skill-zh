---
name: dotnet-codegraph-indexer
description: .NET 项目 CodeGraph 索引管理工具。检测目标项目 CodeGraph 环境、建立/刷新代码知识图索引，产出索引状态与元数据文件，供 dotnet-route-mapper 与 dotnet-route-tracer 调用链加速使用。
---

# .NET CodeGraph 索引管理

## 目标

对目标 .NET 项目建立或刷新 CodeGraph 本地代码知识图索引（`.codegraph/`），使后续 `dotnet-route-mapper` 与 `dotnet-route-tracer` 能通过 `codegraph_explore` / `codegraph_callers` / `codegraph_impact` 获取跨文件调用链，替代部分手动的 grep + Read 组合。

## CRITICAL：索引不是审计替代

- CodeGraph 是**执行层加速工具**，不是审计规则本身
- 路由识别、参数绑定、Sink 判定、证据闭合仍由现有 Skill 负责
- 无 CodeGraph 索引时，100% 回退现有静态分析流程

## 核心输入

用户提供：

- `source_path`：.NET 项目、解决方案或仓库根目录

## 输出目录结构

```text
{output_path}/
├── codegraph/
│   └── codegraph_index_status_{timestamp}.md
└── quality/
    └── codegraph_index_validation_{timestamp}.md
```

## 执行步骤

### 步骤 1：检测 CodeGraph 环境

1. 检查目标目录 `source_path` 下是否已存在 `.codegraph/` 目录
   - 若存在：读取 `.codegraph/codegraph.db` 文件修改时间，记录 `index_exists: true`
   - 若不存在：记录 `index_exists: false`
2. 检测系统 PATH 中是否存在 `codegraph` 命令
   - 若存在：记录 `cli_available: true`，并获取版本号
   - 若不存在：记录 `cli_available: false`

### 步骤 2：索引建立或刷新

#### 场景 A：已存在 `.codegraph/` 且 CLI 可用

- 执行 `codegraph sync {source_path}` 进行增量更新
- 记录 `sync_status` 与更新时间戳

#### 场景 B：无 `.codegraph/` 但 CLI 可用

- 执行 `codegraph init {source_path}` 建立完整索引
- 记录 `init_status` 与耗时

#### 场景 C：CLI 不可用

- 在 `codegraph_index_status_{timestamp}.md` 中记录 `codegraph_status: NOT_AVAILABLE`
- 给出安装指引（不影响后续流程，后续 Skill 回退到现有静态分析）

### 步骤 3：索引质量校验

无论索引是否新建，执行以下校验：

1. **文件覆盖校验**：检查 `.codegraph/` 下 `codegraph.db` 是否存在且非空
2. **C# 符号提取校验**：通过 `codegraph query --kind class --limit 5`（或等效方式）确认 C# 类符号已提取
3. **路由识别校验**：通过 `codegraph explore "ASP.NET controllers and routes"`（或等效查询）确认路由级符号可被检索
4. **关键文件覆盖**：确认 `source_path` 下 `.cs` 文件数量与索引中文件数量对比，记录覆盖率

### 步骤 4：索引元数据记录

将索引信息写入 `codegraph/codegraph_index_status_{timestamp}.md`：

```md
# CodeGraph Index Status

- source_path: {source_path}
- timestamp: {timestamp}
- codegraph_status: {AVAILABLE|NOT_AVAILABLE|INIT_FAILED|SYNC_FAILED}
- cli_version: {version or N/A}
- index_exists: {true|false}
- init_or_sync: {init|sync|none}
- csharp_file_count_on_disk: {n}
- csharp_file_count_in_index: {n}
- coverage_percent: {n}%
- route_symbols_found: {n}
- controller_symbols_found: {n}
- action_symbols_found: {n}
- notes: {any warnings or failures}
```

## 对下游 Skill 的消费约定

### dotnet-route-mapper 消费方式

- 若 `codegraph_status = AVAILABLE` 且 `route_symbols_found > 0`：
  - 优先通过 `codegraph explore "ASP.NET controllers and routes in {source_path}"` 获取 Controller/Action/路由映射
  - 通过 `codegraph query --kind method` 补充 action 方法列表
  - 将 CodeGraph 返回的路由符号与手动静态分析结果交叉验证，差异项标记 `⚠️需人工复核`
- 若 `codegraph_status != AVAILABLE`：完全回退现有静态分析流程

### dotnet-route-tracer 消费方式

- 若 `codegraph_status = AVAILABLE`：
  - 对每条 `route_id`，优先通过 `codegraph_callers {handler_symbol}` 获取调用链上游
  - 通过 `codegraph_impact {handler_symbol} --depth 3` 获取影响半径（含跨文件调用）
  - 对 DI 链路，通过 `codegraph explore "implementation of {interface_name}"` 定位实现类
  - 将 CodeGraph 调用链与手动 trace 结果合并，CodeGraph 独有的跨文件边标注 `source: codegraph`
- 若 `codegraph_status != AVAILABLE`：完全回退现有 trace 流程

## 共享抓手索引引用

- 默认以 `shared/DOTNET_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 本 Skill 不直接审计漏洞，因此不引用 `EVIDENCE_POINT_IDS.md` 中的 Sink 证据点

## 输入依赖

- 必需：`source_path`
- 无其他上游依赖；本 Skill 位于 pipeline 阶段 0，先于 route-mapper 执行

## 输出

- `codegraph/codegraph_index_status_{timestamp}.md`：索引状态与元数据
- `quality/codegraph_index_validation_{timestamp}.md`：索引质量校验结果

## 检查点设计

- 🔴 **CHECKPOINT A（环境检测）**：确认 `codegraph` CLI 可用性与 `.codegraph/` 存在性
- 🔴 **CHECKPOINT B（索引质量）**：确认 C# 符号已提取、路由级符号可检索
- 🟡 **CHECKPOINT C（降级确认）**：若索引不可用，确认下游 Skill 已知晓并回退

## 失败与降级分支

| 触发条件 | 一线处理 | 仍失败的兜底 |
|---|---|---|
| `codegraph` CLI 未安装 | 输出安装指引，标记 `codegraph_status: NOT_AVAILABLE` | 不影响后续流程，下游 Skill 走静态分析 |
| `codegraph init` 失败 | 记录错误日志，标记 `codegraph_status: INIT_FAILED` | 下游 Skill 走静态分析 |
| C# 符号提取为空 | 检查 `.cs` 文件是否存在，若存在则标记 `PARTIAL` | 下游 Skill 走静态分析 |
| 路由符号识别为 0 | 确认项目是否真为 ASP.NET 项目；若不是则标记 `NOT_APPLICABLE` | 若是 ASP.NET 项目但识别为 0，标记 `PARTIAL` |

## 不要做的事

- 反模式：因 CodeGraph 索引失败而阻断整个 pipeline。正确做法：标记状态并回退。
- 反模式：用 CodeGraph 结果替代 route-mapper 的完整输出。正确做法：仅作为加速输入，最终 routes/params 仍由 route-mapper 统一格式化输出。
- 反模式：在索引阶段做 Sink 判定或漏洞分析。正确做法：仅建立索引，审计留给后续 Skill。
