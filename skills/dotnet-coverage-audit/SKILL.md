---
name: dotnet-coverage-audit
description: .NET 代码审计覆盖补检阶段 Skill。接收 Scan 阶段输出的 risks 和 safe_regions，计算未覆盖代码片段（gap），将较大的 gap 送回 Scan 阶段补检。不负责安全判断，只负责覆盖责任追踪。
---

# .NET 覆盖补检（Coverage）

## 目标

根据 Scan 阶段输出的 `risks` 和 `safe_regions`，**计算未覆盖代码片段（gap）**，将较大的 gap 送回 Scan 阶段补检。

**Coverage 不是安全证明，而是责任追踪。**
模型不能只说"我看完了"，它要用风险区域和安全区域交代自己覆盖了哪里。

## 核心原则

- Coverage **不判断语义是否完整**，只计算物理覆盖
- Coverage **不证明代码安全**，只追踪"哪里还没看过"
- 未覆盖的代码片段必须送回 Scan 阶段补检，不能跳过

## 输入

- `scan_audit/scan_{filename}_{timestamp}.md`：Scan 阶段输出的 risks + safe_regions
- `source_path`：项目源码路径
- `min_gap`：最小 gap 阈值（默认 10 行）
- `max_rounds`：最大补检轮次（默认 3 轮）

## 算法逻辑

### 1. 计算未覆盖范围

```
文件总行数 = 文件实际代码行数（排除空行和纯注释行）
已覆盖范围 = risks.line_range ∪ safe_regions.line_range
未覆盖范围 = 文件总行数 - 已覆盖范围
```

### 2. 过滤与合并 gap

- 小于 `min_gap` 行的 gap 忽略（避免过度补检细碎片段）
- 相邻 gap（间隔 < 5 行）合并为一个

### 3. 补检循环

```
for round = 1 to max_rounds:
    gaps = find_uncovered_ranges(file, risks, safe_regions, min_gap)
    if gaps 为空 或 gaps 与上一轮相同:
        break
    for each gap in gaps:
        将 gap 送回 Scan 阶段，要求对这段代码进行扫描
    更新 risks 和 safe_regions
```

### 4. 停止条件

满足以下任一条件时停止补检：
- 无 gap
- gap 与上一轮不变（收敛）
- 达到 `max_rounds` 上限
- 用户显式终止

## 输出 Schema

### 1. coverage_audit/coverage_{filename}_{timestamp}.md

每个文件必须输出一个覆盖报告：

| 字段 | 说明 |
|------|------|
| `file_total_lines` | 文件总行数 |
| `risks_count` | 发现风险数 |
| `safe_regions_count` | 已标记安全区域数 |
| `gaps` | 未覆盖片段列表（每个 gap 含 start_line, end_line, line_count） |
| `rounds_executed` | 实际执行补检轮次 |
| `final_coverage_percent` | 最终覆盖百分比 |
| `stop_reason` | 停止原因 |

### 2. coverage_audit/backfill_{round}_{filename}_{timestamp}.md

每轮补检的详细记录：

| 字段 | 说明 |
|------|------|
| `round` | 补检轮次 |
| `gap_ranges` | 本轮补检的 gap 范围 |
| `new_risks_found` | 本轮新发现的风险 |
| `new_safe_regions` | 本轮新标记的安全区域 |
| `remaining_gaps` | 补检后仍存在的 gap |

## 与下游阶段的衔接

```
Scan 输出 (risks + safe_regions)
    → Coverage 计算 gap
    → 大 gap 送回 Scan 补检
    → 更新 risks / safe_regions
    → Coverage 输出最终覆盖报告
    → 交给 AttackSurface 阶段按风险类型路由
```

## 质量门禁

- [ ] 每个文件都有 coverage_{filename}_{timestamp}.md 输出
- [ ] gap 计算基于实际的行号范围，不是估算
- [ ] 补检轮次不超过 max_rounds
- [ ] 停止原因明确记录
- [ ] 最终覆盖百分比可计算

## 输出路径

- `coverage_audit/coverage_{filename}_{timestamp}.md`
- `coverage_audit/backfill_{round}_{filename}_{timestamp}.md`
- `coverage_audit/index_{timestamp}.md`（批次总索引）
