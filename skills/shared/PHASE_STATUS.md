---
name: phase-status
description: P 阶段交付状态单一真源，pipeline / agent 引用「交付态」的统一口径。
---

# PHASE_STATUS — 交付态单一真源

> 所有 pipeline / agent 引用「P 阶段交付状态」处统一读取本文件，禁止在各处散写时间耦合措辞。
> 更新时机：新增/交付 skill 后必须同步本文件（grep 全仓库 `DEFERRED(P` 回扫动作）。

| Skill | 交付态 | 说明 |
| ---- | ---- | ---- |
| node-express/koa/fastify/nextjs/nuxt/nestjs/graphql-audit | ACTIVE | P2 已交付 |
| cross-stack-taint-linker / cross-stack-consistency-audit | ACTIVE | P2 已交付 |
| node-review-agent | ACTIVE | P1 交付（2026-08-23） |
| node-scan-audit / node-coverage-audit / node-briefing-agent / node-exploit-chain-audit | ACTIVE | P3 交付（2026-09-04） |
| node-codegraph-indexer | ACTIVE | P3 交付（2026-08-23） |
| node-漏洞专项 #27-47（21 项） | ACTIVE | P3 交付（2026-09-04） |
| dotnet-query-injection-audit | ACTIVE | 2026-09-14 台账轮交付（已批准->已实现待验证） |
| dotnet-spreadsheet-export-audit | ACTIVE | 2026-09-14 台账轮交付（已批准->已实现待验证） |
| dotnet-ai-prompt-audit | ACTIVE | 2026-09-14 台账轮交付（已批准->已实现待验证） |
| node-spreadsheet-export-audit | ACTIVE | 2026-09-14 台账轮交付（已批准->已实现待验证） |
| node-ai-prompt-audit | ACTIVE | 2026-09-14 台账轮交付（已批准->已实现待验证） |
| node-feature-api-mapper | ACTIVE | 2026-09-19 第四十三轮交付（已批准->已实现待验证） |

**运行时探测规则**：执行时以「技能是否存在」为准——`skills/` 下无对应目录 → 该技能不可用 → 记 `NOT_RUN + 原因`（或按降级指令适配），禁止按本表之外的旧时间措辞预判。

**manifest 里程碑行格式（唯一真源）**：`阶段 N: DONE ({产物数} files, {关键状态字段} | {timestamp})`
示例：`阶段 3: DONE (34 files, api_coverage_status=COMPLETED | 2026-09-17T15:40:00)`
dotnet / node / fullstack pipeline 引用本格式，禁止在各 skill 散写字面变体。
行内时间戳一律取 run_timestamp（2026-09-21）：fullstack 编排模式即编排层下发值；单栈模式即执行者自产 timestamp——禁止以子栈实际启动时刻替代。

**manifest 映射表格式（2026-09-21，fullstack 强制）**：fullstack 模式下双栈 `quality/manifest_*.md` 必须含 run_timestamp 与实际启动时刻的映射表，列头固定：

| run_timestamp | 子栈实际启动时刻 | 偏差(分钟) |
| ---- | ---- | ---- |
| 2026_09_20_10_38 | 2026_09_20_11_45 | +67 |

`阶段 0.7 复核: AGREE ({命中数}) | {timestamp}` / `阶段 0.7 复核: MISMATCH ({命中目录数}) | {timestamp}`（`design_intent_recheck` 否定结论复核，语义见 AUDIT_EXECUTION_COMMON.md §9 规则⑤）

**等待超时公式（2026-09-20，唯一真源）**：编排层等待子流水线阶段汇报的预期时长，FULL 模式按 `预计分钟 = 2 + 总文件数千分位 × 8` 计算（总文件数 ÷ 1000，每千文件约 8 分钟；例：8110 文件 ≈ 67 分钟）。取整规则（2026-09-21）：计算过程不取整连续计算，结果四舍五入到分钟。总文件数口径（2026-09-21）：GC6 排除目录（`node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`、`coverage/` 及 lockfile 例外项）不计入，计源代码 / 配置 / 前端资产。超时未收到汇报 → 仅允许一次主动核查（不得升级为周期性磁盘轮询），并在 manifest 记录核查原因，记录格式：`超时核查: 阶段 {N} 超过预计 {m} 分钟未汇报 | 核查原因={...} | {timestamp}`。fullstack-audit-pipeline 引用本公式，禁止散写估算口径。
