---
name: node-supply-chain-audit
description: Node.js 供应链安全审计工具。基于 npm audit --json/osv-scanner 输出与 lockfile 漂移分析，识别已知 CVE 命中、postinstall 脚本、typosquatting 与依赖混淆风险，输出分级、证据和修复建议。
---

# Node.js 供应链安全审计

## 共享抓手索引引用

- 默认以 `shared/NODE_AUDIT_GRABBER_INDEX.md` 作为本 Skill 的基础检索索引
- 默认以 `shared/NODE_SINK_REFERENCE.md` 作为本专项 Sink 类型定义与 trace-gate 校验基准
- **默认遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的通用执行标准（二阶段判定、fail-close 判定、命中 ID 规范、测试要求）**
- **以 `shared/NODE_SUPPLY_CHAIN_CRITERIA.md` 作为本专项判定标准真源（确认 / 待确认 / 误报三档口径）**
- 默认以 `shared/SEVERITY_RATING.md` 作为分级与编号规范
- 默认以 `shared/IO_PATH_CONVENTION.md` 作为产物路径与命名规范
- 枚举时至少覆盖与依赖声明、lockfile、包源配置、install 脚本相关的共享抓手
- 若项目存在私有 registry、monorepo workspace 或内部包仓库，必须补充到输出中的项目内抓手章节
- 当本 Skill 的专项枚举规则比共享索引更细时，以本 Skill 为准，但不得缩减共享索引的基础覆盖范围

## 输入依赖

- 必需：`node_source_path`
- 可选：`node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/params_{timestamp}.md`（用于对齐受影响入口与 `route_id`）
- 可选：`node/route_mapping/middleware_inventory_{timestamp}.md`（用于确认中间件覆盖顺序与短路条件）
- 可选：`node/auth_audit/auth_mapping_{timestamp}.md`（用于补充匿名入口、P0/P1 分桶、鉴权边界或业务前置条件）
- 可选：`node/framework_audit/*_{timestamp}.md`（用于补充宿主、框架控制面、静态目录或运行时边界）
- 可选：`cross/api_contract_map_{timestamp}.md`（用于跨端依赖面与构建产物联动分析）
- 本专项属于 **静态证据驱动**：`node/route_tracer/{route_id}/trace_{timestamp}.md` 与 `node/route_tracer/{route_id}/trace_summary_{timestamp}.md` 仅作为交叉证据，不是前置硬依赖；但运行时可达性判定须结合 route-trace 与打包产物分析（口径见 `shared/NODE_SUPPLY_CHAIN_CRITERIA.md`）
- 如通过 `dotnet-audit-pipeline`（Node.js 扩展模式）执行，当前专项引用的 `route_id` 应与 `node/cross_analysis/high_risk_routes_{timestamp}.md` 保持一致

## 重点检查

- 工具初筛：`npm audit --json` / `osv-scanner` 输出（`EVID_NODE_SUPPLY_TOOL_OUTPUT`）
- lockfile（package-lock.json / yarn.lock / pnpm-lock.yaml）与 package.json 漂移、lockfile 缺失
- install 脚本：`preinstall` / `postinstall` / `prepare` 执行任意命令
- typosquatting 特征：包名与流行包高度相似、registry 无发布历史
- 依赖混淆：内部包名未配置 scope 私源映射，可被公网 registry 抢注
- 直接/间接依赖可达性：漏洞包是否被运行时 `require` / `import` 加载，还是仅 devDependencies

## 枚举规则（强制细化）

- 枚举依赖声明：`package.json`、`package-lock.json`、`yarn.lock`、`pnpm-lock.yaml`、`.npmrc`
- rg 搜索：`dependencies`、`devDependencies`、`scripts`、`preinstall`、`postinstall`、`prepare`、`registry`、`require(`、`import `
- 工具命令：`npm audit --json`、`osv-scanner --format json`；工具不可用时记录原因并按 lockfile 逐包比对 OSV/GHSA，标注 `待验证`
- 对每个命中包记录：包名、locked 版本、CVE/GHSA、影响区间、修复版本、直接/间接、运行时可达性
- typosquatting / 依赖混淆以 registry 流行度与来源声明为基准，命中标注 `待验证` 并人工复核
- 若依赖经 monorepo workspace 或别名校验，必须逐层展开到真实安装来源

## Barrier 验证矩阵（强制）

| Barrier 类型 | 典型实现 | 验证动作 | 判定标准 |
| ---- | ---- | ---- | ---- |
| 工具初筛 | `npm audit --json` / `osv-scanner` | 运行工具并留存原始 JSON 输出 | 产出可解析输出 → ✅ 初筛证据；工具不可用 → 记录原因并回退人工比对 ⚠️ |
| 版本锁定 | package-lock.json / yarn.lock / pnpm-lock.yaml | 对比 lockfile 与 package.json range 漂移 | lock 提交且无漂移 → ✅ 安全；缺失或漂移 → 🔴 高危 |
| 运行时可达性 | `require` / `import` 加载路径与打包产物 | 追踪漏洞包是否进入运行时加载路径 | 运行时可达且无缓解 → 维持结论；仅 devDependencies 且不进产物 → 降级 |
| 来源可信 | `.npmrc` registry / scope 映射 | 核对私有 scope 与内网源映射、包名拼写 | scope 显式映射 → ✅ 安全；无声明且名称相似 → ⚠️ typosquatting/混淆嫌疑 |

## 二阶段判定（强制）

本专项遵循 `shared/DOTNET_AUDIT_EXECUTION_STANDARD.md` 的二阶段判定流程：

> 通用执行标准以 `shared/AUDIT_EXECUTION_COMMON.md` 为真源（shared 演进决策 3），本节保留 node 栈特定差异。

### 阶段一：临时结论

对每条命中先给出三选一临时结论：

- `确认漏洞候选`：漏洞依赖疑似存在于 lockfile 并可能在运行时加载路径可达
- `待确认`：上下文显示可疑模式，但外部输入来源、barrier 行为或调用链不清晰
- `误报`：输入来自固定常量 / 枚举映射，或 barrier 已验证为 fail-close

### 阶段二：强制追证

若阶段一为「待确认」，必须继续向下追至少一跳调用链或下游解析器，直到满足以下任一条件：

- 找到漏洞依赖在运行时加载路径可达且无有效缓解的证据 → `确认漏洞`
- 找到固定白名单映射 / fail-close 证据 → `误报`
- 仍缺少关键调用链 → 保持 `待确认`，但必须说明缺失哪一跳

**fail-close 语义**：对 barrier、白名单、校验器、过滤器必须以失败模式评估。未知 / 非法输入必须抛异常、返回空、拒绝执行或日志告警，绝不能透传原始值；任何 silent-fallback 或 fail-open 行为均视为高危。

## 判定规则（强制细化）

### 已确认

- `EVID_NODE_SUPPLY_TOOL_OUTPUT` + lockfile 版本命中已知 CVE/GHSA + 依赖在运行时加载路径可达 + 无有效缓解（版本修复/替代包）
- `EVID_NODE_SUPPLY_TOOL_OUTPUT` + `postinstall` 等安装期脚本命中任意命令执行或下载器特征

### ⚠️待验证

- CVE 影响版本区间与 locked 版本交集不明，需人工比对修复版本
- 运行时可达性证据不足（缺 `require`/`import` 调用链或打包产物分析）
- typosquatting / 依赖混淆嫌疑命中，registry 流行度与来源声明未复核

### 误报

- locked 版本已高于修复版本，CVE 不再影响
- 漏洞包仅为 devDependencies 且不进入构建产物与运行时
- 包名拼写正确、scope 映射内网源，排除 typosquatting 与依赖混淆嫌疑

## 测试建议（强制）

### 正向测试

- 对含已知 CVE 的 locked 版本复现 `npm audit --json` 命中并关联运行时调用链
- 构造 `postinstall` 下载器脚本验证安装期执行面
- 测试用例标注 `test_id`，与命中 ID 关联

### 负向测试

- 已修复版本与仅 devDependencies 场景应输出 `误报` 并附判定依据
- scope 私源映射正确时，同名公网包不可安装成功

### 回归测试

- 修复后复测 lockfile 无版本漂移、无新增 install 脚本
- 工具版本升级后复核命中区间口径未变化

## 证据引用

- `EVID_NODE_SUPPLY_TOOL_OUTPUT`

## 输出

- `node/vuln_audit/supply-chain_{timestamp}.md`
- `node/vuln_poc/supply-chain_{timestamp}.md`（供应链 PoC 多为版本/来源证据与复现步骤：CVE/GHSA 编号、影响区间、locked 版本、install 脚本复现命令；非运行时请求模板）
