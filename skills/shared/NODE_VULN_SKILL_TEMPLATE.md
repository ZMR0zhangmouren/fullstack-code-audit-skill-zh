# Node.js 漏洞专项 Skill 模板

本模板用于新增 node-{type}-audit 类漏洞专项 Skill，供 P1 Node.js 全栈扩展各漏洞专项起稿使用。

## 使用说明

- 将 {type} 替换为具体漏洞类型标识（如 sql、cmd、ssrf、xss 等）
- 根据专项需要补充重点检查、枚举规则、Barrier 验证矩阵、判定规则、测试建议、证据引用和输出要求
- 默认接入 shared/NODE_AUDIT_GRABBER_INDEX.md、shared/NODE_SINK_REFERENCE.md、shared/SEVERITY_RATING.md、shared/IO_PATH_CONVENTION.md
- **必须显式遵循 shared/DOTNET_AUDIT_EXECUTION_STANDARD.md 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）；该标准栈无关，Node.js 侧直接引用**
- 必须显式写出 `## 输入依赖`，不要把 `node_source_path`、`node/route_mapping/*`、`node/route_tracer/*`、`node/auth_audit/*` 的关系留成隐含约定
- 若该专项属于 trace-gate 类型，应在 `## 输入依赖` 中写明优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`，并可选消费 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`
- 若该专项属于静态证据驱动类型，应在 `## 输入依赖` 中写明 `node/route_tracer/*` 仅作为交叉证据而不是硬前置条件
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，应在 `## 输入依赖` 中写明当前专项引用的 `route_id` 必须与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致
- 若专项与鉴权、匿名入口或 P0/P1 排序有关，应把 `node/auth_audit/auth_mapping_{timestamp}.md` 写为可选输入
- 若专项会受宿主、框架控制面、序列化配置、静态目录或中间件顺序影响，应把 `node/framework_audit/*_{timestamp}.md` 写为可选输入
- 若存在跨端联动场景（前端参数、API 契约、BFF 转发），应把 `cross/api_contract_map_{timestamp}.md` 写为可选输入
- 如具备可复现条件或至少可构造待验证请求，应同时生成 `node/vuln_poc/{type}_{timestamp}.md`，并参考 shared/DOTNET_VULN_POC_TEMPLATE.md（PoC 结构栈无关，Node.js 侧直接引用）
- 若该专项依赖 route_tracer 或 framework_audit，必须在正文中明确其消费关系
- 若该专项需要新增 EVID_NODE_* 或新的 shared 抓手，应先更新 shared 再落 Skill

## 模板

```md
---
name: node-{type}-audit
description: Node.js {type} 审计工具。识别 ... 风险，输出分级、证据和修复建议。
---

# Node.js {type} 审计

## 共享抓手索引引用

- 默认以 shared/NODE_AUDIT_GRABBER_INDEX.md 作为本 Skill 的基础检索索引
- 默认以 shared/NODE_SINK_REFERENCE.md 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 shared/DOTNET_AUDIT_EXECUTION_STANDARD.md 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 shared/SEVERITY_RATING.md 作为分级与编号规范
- 默认以 shared/IO_PATH_CONVENTION.md 作为产物路径与命名规范
- 枚举时至少覆盖与 {type} 相关的共享抓手
- 若项目存在二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、序列化配置、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 若属于 trace-gate 专项：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 若属于静态证据驱动专项：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖
- 如通过 pipeline 执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- ...

## 枚举规则（强制细化）

- ...

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| ... | ... | ... | ... |

## 二阶段判定（强制）

本专项遵循 shared/DOTNET_AUDIT_EXECUTION_STANDARD.md 的二阶段判定流程：

> 通用执行标准以 shared/AUDIT_EXECUTION_COMMON.md 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入 Sink 构造或敏感操作点
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

- ...

### ⚠️待验证

- ...

### 误报

- ...

## 测试建议（强制）

### 正向测试

- ...

### 负向测试

- ...

### 回归测试

- ...

## 证据引用

- EVID_NODE_...

## 输出

- `node/vuln_audit/{type}_{timestamp}.md`
- `node/vuln_poc/{type}_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
```

## 最低验收要求

- 名称、description、职责边界清晰
- 已引用 shared/NODE_AUDIT_GRABBER_INDEX.md、shared/NODE_SINK_REFERENCE.md、shared/DOTNET_AUDIT_EXECUTION_STANDARD.md、shared/SEVERITY_RATING.md、shared/IO_PATH_CONVENTION.md
- 已具备完整十层结构：共享抓手索引引用 + 输入依赖 + 重点检查 + 枚举规则（强制细化）+ Barrier 验证矩阵（强制）+ 二阶段判定（强制）+ 判定规则（强制细化）+ 测试建议（强制）+ 证据引用 + 输出
- 已说明证据引用口径（含 EVID_NODE_* 占位或真实证据点）
- 已说明与 node/route_tracer / node/framework_audit / pipeline / cross 端的关系
- 已写明该专项是 trace-gate 还是静态证据驱动，以及 `node/route_tracer/*` 属于硬前置还是交叉证据
- Barrier 验证矩阵列头严格为 `| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |`
- 输出路径符合 shared/IO_PATH_CONVENTION.md，且明确写为 `node/vuln_audit/{type}_{timestamp}.md` 与 `node/vuln_poc/{type}_{timestamp}.md`
- 如存在可复现或可构造请求模板，应同时给出 vuln_poc 产物
- 能与现有专项区分边界，不产生大面积重复职责
