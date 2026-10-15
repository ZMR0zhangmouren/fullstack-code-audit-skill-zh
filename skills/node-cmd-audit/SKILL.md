---
name: node-cmd-audit
description: Node.js 命令执行审计工具。识别 child_process.exec/execSync/spawn(shell:true)/execFile 拼接与 shell 解释风险，输出可利用性分级、PoC 与修复建议。
---

# Node.js 命令执行审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与命令构造、shell 选择、参数传递、参数数组化相关的共享抓手
- 若项目存在 ShellHelper、CommandRunner、ScriptExecutor 等二次封装，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐入口、参数绑定与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、序列化配置、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端参数来源、字段映射与上下游联动分析）
- 本专项属于 **trace-gate**：优先消费 `node/route_tracer/{route_id}/trace_{timestamp}.md`；如存在 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md`，可作为摘要索引
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- `child_process.exec` / `execSync` 拼接
- `spawn` / `execFile` 的 `shell:true`
- 参数数组化缺失

## 枚举规则（强制细化）

- 枚举所有 `child_process`、`exec(`、`execSync(`、`spawn(`、`execFile(`、`fork(`、`shell: true`、`shell:true` 调用点
- 对每个执行点记录：命令构造方式、参数来源、是否经过白名单、是否使用 shell 解释、宿主平台、服务账户权限
- 区分整串拼接（`exec(command)`）与参数数组化（`execFile(file, args)` / `spawn(command, args, {shell:false})`）
- 记录 `options.shell` 显式值、默认值及用户输入是否进入 `command` 字符串或 `args` 数组元素
- 识别参数数组化被错误混用的场景：单参数位内存在字符串插值或 `shell:true` 重新开启 shell 解释
- 若存在二次封装，必须逐层展开到真实 `child_process` 调用点

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 参数数组化 | `child_process.execFile` / `spawn` 默认 `shell:false` | 检查调用点是否使用数组参数并关闭 shell 解释 | 数组化且 `shell:false`，无单参数插值 → ✅ 安全；仍用 `exec` / `execSync` 或显式 `shell:true` → 🔴 高危 |
| 命令白名单 | 命令 / 参数 allowlist | 读取白名单实现源码，确认是否为 fail-close（未知命令拒绝执行） | fail-close（枚举外拒绝 / 抛异常） → ✅ 安全；fail-open（默认允许 / 回退） → ⚠️ 可绕过；无白名单 → 🔴 高危 |
| shell 默认关闭 | `spawn` / `execFile` 的 `options.shell` | 检查 `options.shell` 显式值与默认行为 | `shell:false` 或无 shell 选项 → ✅ 安全；`shell:true` 且参数可控 → 🔴 高危 |
| 输入校验 | joi / zod / 正则白名单 | 检查校验器是否覆盖命令字符串 / 参数来源并拒绝非法输入 | fail-close 校验 → ✅ 安全；校验可被截断 / 编码 / 元字符绕过 → ⚠️ 待确认；无校验 → 🔴 高危 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：外部可控输入疑似进入命令字符串拼接或 shell 解释参数位
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

- `EVID_NODE_CMD_EXEC_POINT` + `EVID_NODE_CMD_USER_PARAM_TO_CMD` + 无有效 Barrier
- 外部可控参数直接进入命令字符串拼接位置，且无 barrier 验证
- `spawn` / `execFile` 显式设置 `shell:true` 且用户输入进入命令或含 shell 元字符的参数位
- 命令白名单为 fail-open 或 silent-fallback，外部可控输入可绕过白名单进入 Sink

### ⚠️待验证

- 上下文显示可疑模式（如 `child_process.exec` 调用），但外部输入来源不清晰（需补 trace 或调用链）
- Barrier 函数（如白名单、输入校验）存在，但当前分支是否调用、返回值是否被使用无法确认
- 参数数组化与整串拼接混用，但当前调用点无法确认具体使用路径

### 误报

- 参数完全静态或 allowlist 不可绕过（fail-close）
- 使用 `execFile` / `spawn` 参数数组化且 `shell:false`，每个参数位均来自固定常量或已验证的白名单输出
- 命令字符串来自固定常量 / 枚举映射，未知输入会拒绝执行（fail-close）

## 测试建议（强制）

### 正向测试

- 构造确认可利用的命令注入输入：`; cat /etc/passwd`、`&& whoami`、`$(id)`、`| dir`、`\`whoami\``
- 验证用户参数进入 `exec` / `execSync` 整串或 `shell:true` 场景下的命令执行
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 构造被 barrier 拦截的输入：白名单外命令、非法 shell 元字符、超长参数
- 验证参数数组化 / `shell:false` 场景下 shell 元字符被当作普通参数处理
- 验证 joi / zod / 正则白名单对非法输入明确拒绝

### 回归测试

- 修复后复测，确认 barrier 仍然生效
- 复测 `execFile` / `spawn` 参数数组化与 `shell:false` 配置，确认未引入新的绕过路径
- 验证命令白名单新增命令时仍保持 fail-close

## 证据引用

- `EVID_NODE_CMD_EXEC_POINT`
- `EVID_NODE_CMD_STRING_CONSTRUCTION`
- `EVID_NODE_CMD_USER_PARAM_TO_CMD`
- `EVID_NODE_CMD_ARG_ARRAY_OR_ALLOWLIST`

## 输出

- `node/vuln_audit/cmd_{timestamp}.md`
- `node/vuln_poc/cmd_{timestamp}.md`（已确认 / 待验证 / 环境依赖 PoC）
