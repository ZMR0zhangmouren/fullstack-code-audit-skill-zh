---
name: node-feature-api-mapper
description: UI 功能面↔API 映射采集工具。从 SPA 路由表与组件树 import 链出发，建立「功能面 → 前端 client 方法 → (method, path) 端点 → 后端 route_id」三层映射，产出 node/route_mapping/feature_api_map_{timestamp}.md，供逻辑审计按功能面组织判定与鉴权敏感度分级参照。
---

# Feature ↔ API Mapper

## 共享抓手索引引用

本 Skill 的路径与产物命名遵循 `skills/shared/IO_PATH_CONVENTION.md` 中 `node/` 子树约定；枚举口径与上游 node-route-mapper 产物（`routes_{timestamp}.md` / `frontend_outbound_{timestamp}.md`）保持一致，不重复发明采集规则。

## 目标

建立功能面→端点→后端 route_id 三层映射：

1. **功能面**：SPA 路由 / 页面组件对应一个用户可感知的功能（备份、导出、租户管理等）。
2. **端点**：该功能在组件树中实际调用的前端 client 方法与其 (method, path) 端点。
3. **后端 route_id**：端点在 node routes 产物或 contract_map 中的后端路由标识，供 tracer / logic-audit 反查。

**产物定位红线（与 design_intent 同，强制）**：本 Skill 全部产物属**视图层参考**，**禁止作为 EVID 证据源**（适用 `skills/shared/AUDIT_EXECUTION_COMMON.md` §9 同红线）；产物与代码不一致时**以代码为准**，不一致处登记「功能视图-实现漂移」治理发现，不得反向修改代码事实。本 Skill 只采集与映射，不做漏洞判定。

## 输入依赖

用户提供或上游产物提供：

- `node_source_path`：Node.js 项目根目录（必需）。
- `node/route_mapping/routes_{timestamp}.md` 与 `node/route_mapping/frontend_outbound_{timestamp}.md`（必需，上游 node-route-mapper 产物；本 Skill 复用其路由枚举与前端外呼采集结果，不重复枚举）。
- `cross/api_contract_map_{timestamp}.md`（fullstack 模式可选；matched 桶为端点→后端 route_id 的优先对齐源）。
- `node/design_intent/design_intent_{timestamp}.md`（可选；用于功能名启发式的业务规则关键词匹配与「design_intent 对齐引用」列填充）。

## 采集规则 ①：SPA 路由表扩展

- **路由声明源**：React Router 路由声明（`Routes.tsx` / `route*` 配置文件 / 框架等价物），排除 `node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`、`coverage/`。
- **功能名列**：在既有路由表三列（路径 / 组件 / 守卫）上扩展第四列**功能名**。
- **功能名启发式三依据**（按优先级）：
  1. 路由 path 尾段语义（如 `/backup` → 「备份管理」）。
  2. 页面组件名语义（如 `BackupPage` → 「备份管理」）。
  3. design_intent 业务规则清单关键词匹配（命中时记录规则编号）。
- **逐条标注命名依据**：每条功能必须标注 `命名依据`（path 段 / 组件名 / design_intent 规则编号）；三依据均无命中时写 `启发式（非证据）`，不得伪装成有据命名。

## 采集规则 ②：组件树 import 反向索引

- 从路由表页面组件出发，递归解析 import 链（页面组件 → 子组件 → …），**最大深度 6 层防循环**；到达深度上限仍未命中调用点的分支记断链原因「间接封装超一层」。
- 命中 api client 调用点（client 方法引用 / `authorizedFetch` 包装调用）即记录三要素：**组件名、调用点 file:line、方法名**。
- 排除 `node_modules/` 与构建产物目录；同组件多调用点逐条记录，不得合并省略。

## 穿透白名单

以下三类识别为**中转层**，穿透一层取其内部真实端点调用：

| 白名单模式 | 典型形态 | 穿透语义 |
| ---- | ---- | ---- |
| `api/index.ts` 类封装模块 | 集中导出 client 方法的 barrel 封装 | 穿透一层，取封装内部对真实端点（`baseUrl + '...'`）的调用 |
| `useXxx` 数据 hook | `useBackup` / `useFetch` 等数据获取 hook | 穿透一层，取 hook 内部对 client 方法或 `authorizedFetch` 的调用 |
| `authorizedFetch` 包装函数 | fetch 统一包装 / 拦截器封装 | 穿透一层，取包装函数内真实请求路径与参数 |

**约束**：每层穿透必须落地到下一层的具体调用点（file:line），穿透深度**仅限一层**；穿透一层后仍无法定位端点的调用点即断链，进 `unmapped_feature_calls_{timestamp}.md`，不得继续臆测穿透第二层，不得静默丢弃。

**裁决（2026-09-19）**：client 方法定义体（barrel 内部端点字面量）的解析属采集规则③（复用 `node-route-mapper`「frontend_outbound 出站端点采集」节 rg 规则），不计穿透层数。

## 断链兜底（强制）

穿透后仍无法定位端点的调用点，逐条落入 `node/route_mapping/unmapped_feature_calls_{timestamp}.md`，每条含（组件、调用点 file:line、断链原因）。断链原因三分类：

1. **动态字符串端点**：端点为模板变量或运行时值（如 `` `/api/${mod}` ``），静态解析无法闭合。**归类优先级（2026-09-19 裁决）**：端点为模板变量/插值整体、静态完全不可求值时归本类（①）；路径主体可静态确定、仅因多片段拼接或条件分支无法还原最终路径时归「运行时拼接」（③）。
2. **间接封装超一层**：调用点经白名单外或超出一层的间接封装，无法定位真实端点。
3. **运行时拼接**：端点由多个片段运行时拼接（字符串拼接 / 数组 join / 条件分支拼接），静态无法还原最终路径。

约束（沿用 unmapped 语义）：

- **禁止静默丢弃**：任何未闭合调用点必须出现在 unmapped 清单或映射表中，不得省略。
- `unmapped_count > 0` 时 `coverage_status=PARTIAL`，并建议进入循环补图（每轮刷新映射与 unmapped 清单）；仅当 unmapped 清零或用户显式接受时方可停止。
- `coverage_status=PARTIAL` 时禁止宣称功能视图完整。

## 采集规则 ③：client 方法 → 端点 → 后端 route_id

- **client 方法 → 端点**：复用 `node-route-mapper`「frontend_outbound 出站端点采集」节的 rg 规则（`baseUrl + '...'` 模式 + 生成客户端方法表 + 客户端构造复核，见该 skill 正文），不重复发明。
- **端点 → 后端 route_id**：
  - fullstack 模式：优先消费 `cross/api_contract_map_{timestamp}.md` 的 **matched 桶**；
  - 单栈 node 模式：按 (method, path) 直接对齐 `routes_{timestamp}.md`；
  - 均无匹配写 `backend_route_id: N/A` 并计入断链（进 unmapped 清单）。
- 后端控制器域取自 routes 产物的 handler 归属；无法归属写 `N/A`。

## 产物契约

产物：`node/route_mapping/feature_api_map_{timestamp}.md`。头部强制四字段：

```md
feature_total: {N}
endpoint_link_count: {M}
unmapped_count: {K}
coverage_status: COMPLETE | PARTIAL | NOT_APPLICABLE
```

三节结构完整模板：

```md
# feature_api_map_{timestamp}

feature_total: {N}
endpoint_link_count: {M}
unmapped_count: {K}
coverage_status: COMPLETE | PARTIAL | NOT_APPLICABLE

## 1. 功能清单

| feature_id | 功能名 | SPA 路由 | 页面组件 file:line | 守卫 | design_intent 对齐引用 | 命名依据 |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| F001 | … | … | … | … | 规则编号或「无」 | path 段 / 组件名 / design_intent 规则编号 / 启发式（非证据） |

## 2. 功能→端点映射表

| feature_id | 前端 client 方法 | (method, path) 端点 | backend_route_id | 后端控制器域 | 通道（直连/BFF 中转） |
| ---- | ---- | ---- | ---- | ---- | ---- |
| F001 | … | … | R{序号} 或 N/A | … | 直连/BFF 中转 |

## 3. 覆盖统计与断链

- 各功能端点数分布（min / median / max，及端点数为 0 的功能列表）。
- unmapped_feature_calls 引用路径：`node/route_mapping/unmapped_feature_calls_{timestamp}.md`（unmapped_count > 0 时必须落盘并引用）。
- 覆盖结论：coverage 内功能占比、断链集中在哪些封装模式、下一轮循环补图建议。
```

红线复述：产物属视图层参考，禁止作 EVID 证据源；与代码不一致以代码为准，不一致登记「功能视图-实现漂移」治理发现。

## fail-open

纯 BFF / 无 SPA 前端项目不阻塞：先执行探测证据 rg 命令（如 `rg --files -g 'Routes.tsx' -g 'route*.{ts,tsx,js,jsx}' -g '!node_modules'` 及 `rg -n "createBrowserRouter|<Route|path=" src/`），探测证据（无路由声明文件）落盘说明，产物头部写：

```md
feature_total: 0
endpoint_link_count: 0
unmapped_count: 0
coverage_status: NOT_APPLICABLE
```

并在正文写明探测命令与「无 SPA 路由声明」的判定依据；该说明文件不阻塞 pipeline 后续阶段。

## 验收

1. 头部四强制字段齐备：`feature_total` / `endpoint_link_count` / `unmapped_count` / `coverage_status`。
2. 三节齐全，映射表列名与产物契约模板逐字一致（`feature_id | 前端 client 方法 | (method, path) 端点 | backend_route_id | 后端控制器域 | 通道`）。
3. 功能清单每条有 `命名依据`；无依据条目必须写 `启发式（非证据）`。
4. import 链递归深度 ≤ 6 层；穿透白名单仅穿透一层。
5. `unmapped_count` 与 `unmapped_feature_calls_{timestamp}.md` 条目数一致；断链逐条有三分类原因之一，无静默丢弃。
6. `coverage_status=PARTIAL` 时有循环补图建议；`NOT_APPLICABLE` 时有探测证据 rg 命令与输出。
7. 红线自检：全文无 EVID 定义、无漏洞判定结论；产物定位写明视图层参考、禁止作 EVID 证据源、与代码不一致以代码为准。

## 不要做的事

- 不做漏洞判定、不做 trace（判定与追踪留在 logic-audit / route-tracer）。
- 不做 React 以外框架适配（Vue/Angular 真实需求出现再立项，YAGNI）。
- 不改上游 route-mapper 既有产物结构与 contract-mapper 三桶语义；不重复枚举路由（复用 routes / frontend_outbound）。
- 不新增 EVID ID；产物禁止作 EVID 证据源。
- 不静默丢弃断链调用点；不将启发式命名伪装成有据命名。
