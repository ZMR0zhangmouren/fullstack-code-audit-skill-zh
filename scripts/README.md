# scripts/validate_audit.py — .NET 审计输出门禁校验

独立的程序化质量门禁脚本，把「模型负责产出、脚本负责判门禁」落地：对一次
dotnet-audit-pipeline 审计的输出目录做契约一致性与门禁一致性校验，输出
PASS / FAIL / WARN 三级结果与修复建议。纯 Python 标准库实现
（`re` / `argparse` / `pathlib` / `json`），无第三方依赖，Windows 中文路径可用。

## 用法

```bash
# 基本用法（skill 库根目录默认取脚本所在目录的上一级）
python scripts/validate_audit.py <audit_output_dir>

# 显式指定 skill 库根目录（用于定位 EVIDENCE_POINT_IDS.md）
python scripts/validate_audit.py <audit_output_dir> --skill-root <skill_root>

# 机器可读 JSON 输出（供 CI / 汇总脚本消费）
python scripts/validate_audit.py <audit_output_dir> --json
```

## 退出码约定

| 退出码 | 含义 |
| ------ | ---- |
| 0 | 全部 PASS，或仅存在 WARN（WARN 不阻断交付，但需人工复核） |
| 1 | 存在至少一项 FAIL，门禁未通过 |
| 2 | 用法错误或环境错误（输出目录不存在、EVID 字典不可读等） |

## 检查项与契约出处

| # | 检查项 | 契约出处 |
| - | ------ | -------- |
| A | trace 契约：`route_tracer/**/trace_*.md` 必须含 5 个强制章节（`## 5) 参数可控性矩阵`、`## 6) Sink 定位`、`## 7) Sink Summary`、`## 8) Trace 完整性声明`、`## 9) Sink Evidence Type Checklist`）；`trace_status` 必须可解析且 ∈ {COMPLETE, PARTIAL, UNRESOLVED}；`## 9)` 中引用的 `EVID_*` ID 必须已登记 | `skills/dotnet-route-tracer/SKILL.md`「单路由报告模板（强制）」「Trace 状态」；`skills/dotnet-audit-pipeline/SKILL.md` 阶段 3「trace 契约校验」；合法 ID 字典 `skills/shared/EVIDENCE_POINT_IDS.md`（脚本运行时动态解析，不硬编码） |
| B | 占位符残留：递归扫描所有 `.md`，报告未替换的 `${var}` 与 `{{var}}`（单花括号的 `{host}` `{cookie}` `{token}` `{apiKey}` `{jwt}` 及 `{timestamp}` 等模板字段不报错） | `skills/dotnet-audit-pipeline/SKILL.md`「完整性约束」第 2 条；`skills/shared/IO_PATH_CONVENTION.md`「PoC 占位符规则」 |
| C | 门禁一致性：`quality/api_coverage_gate_*.md` 的 `api_coverage_status` / `api_coverage_percent` / `coverage_mode` 与 `quality/pipeline_execution_*.md` 的 `pipeline_execution` 对账——`api_coverage_status != COMPLETE`、FULL 模式下 `percent < 100%`、或 `coverage_mode=SAMPLE` 时，`pipeline_execution=COMPLETED` 判 FAIL | `skills/dotnet-audit-pipeline/SKILL.md`「API Coverage Gate（强制）」「入口覆盖模式与门禁」；`skills/shared/IO_PATH_CONVENTION.md`「覆盖门禁与完成态约定」；`skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md`「验收要点」 |
| D | 最终报告：`*代码审计*.md` 必须同时声明 `audit_surface_status` 与 `api_coverage_status`（双完成态）；`api_coverage_status=PARTIAL` 时必须存在 `quality/unmapped_routes_*.md`；报告中 `EVID_*` 引用合法性同检查 A | `skills/shared/DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md`「固定模板（强制字段）」；`skills/dotnet-audit-pipeline/SKILL.md`「双完成态声明（强制）」「Route Mapping 循环补图门禁」 |
| E | 降级语义：`trace_status=PARTIAL/UNRESOLVED` 的 `route_id` 在 `vuln_audit/*.md` 同条目附近出现「已确认」时报 WARN（文本级近似归因，无法精确到漏洞条目，故按 WARN 而非 FAIL） | `skills/dotnet-audit-pipeline/SKILL.md`「强制约束」「trace 完整性回退规则」；`skills/dotnet-route-tracer/SKILL.md`「失败与降级分支」 |
| F | 阶段目录完整性：按约定应有 16 个阶段目录（codegraph/scan_audit/coverage_audit/route_mapping/auth_audit/route_tracer/briefing/vuln_audit/vuln_poc/framework_audit/cross_analysis/vuln_report/exploit_chain/global_sink_fallback/review/quality），缺失报 WARN；空目录或有产物但无 `index_*` / `empty_result_*` 索引文件报 WARN | `skills/shared/IO_PATH_CONVENTION.md`「默认执行模式（强制落盘）」「阶段索引文件与空结果文件（强制）」；`skills/dotnet-audit-pipeline/SKILL.md`「输出目录结构」 |

## 接入 pipeline 的建议位置

建议在 **阶段 5（汇总报告）定稿之前** 运行本脚本，作为收尾双保险的程序化一环：

```
阶段 4.5 证据质检 → 阶段 5 汇总初稿 → 【python scripts/validate_audit.py <output_path>】
→ 修复 FAIL → 复核 WARN → 落盘 quality/final_anchor_checklist_{timestamp}.md → 交付
```

- 退出码 1（存在 FAIL）时，与 `final_anchor_decision` 的 BLOCKED 语义对齐，禁止输出
  「可交付 / 收尾完成」结论；
- `--json` 输出可直接被后续自动化（如 CI 或汇总 Agent）解析，`results[].check` 字段
  对应上表 A–F 检查项；
- 脚本只读校验，不修改审计输出目录中的任何文件。

## pre-commit 门禁入口（T3-13）

`scripts/pre_commit_check.ps1` 是 pre-commit 场景的门禁检查入口：调用 `validate_audit.py --stack auto` 并**透传退出码**（0=通过/仅WARN 放行，1=有FAIL 阻断，2=用法错误）。默认目标为自测样例基线；传入审计输出目录可校验该次产物。是否接入 git hooks 由使用者决定（`git config core.hooksPath` 指向自建 hooks 目录，或追加到现有 `.git/hooks/pre-commit`），本仓库**不创建 `.github/` workflow**。

```powershell
.\scripts\pre_commit_check.ps1                        # 默认校验自测样例基线（预期退出码 1：样例故意 FAIL）
.\scripts\pre_commit_check.ps1 D:\targets\eshop_audit # 校验指定审计输出目录（0=可提交/交付，1=阻断）
```

## 自测样例 scripts/_demo_audit/

`scripts/_demo_audit/` 是保留的自测样例（非真实审计产物），手工构造了以下反例：

- `route_tracer/R0001/trace_*.md`：缺 `## 9)` 章节 → 检查 A FAIL
- `route_tracer/R0002/trace_*.md`：`trace_status=UNRESOLVED` 且 `## 9)` 引用伪造的
  `EVID_SQL_TOTALLY_FAKE_ID` → 检查 A FAIL
- `demo_代码审计_*.md`：含 `${gate_reason_text}`、`${user_id}`、`{{session_cookie}}`
  残留 → 检查 B FAIL；声明 `api_coverage_status=PARTIAL` 但缺 `unmapped_routes_*.md`
  且引用伪造 `EVID_SQL_FAKE_POINT` → 检查 D FAIL
- `quality/pipeline_execution_*.md`：`pipeline_execution=COMPLETED` 与
  `api_coverage_status=PARTIAL` / `percent=80%` 冲突 → 检查 C FAIL
- `vuln_audit/sql_*.md`：`trace_status=PARTIAL` 的 R0001 被标 ✅已确认 → 检查 E WARN
- 大量阶段目录缺失 / 缺 index 文件 → 检查 F WARN

契约漂移反例套件（2026-08-23 按栈分套补充）：

- `dotnet_missing_section/`：trace 缺强制章节 `## 7) Sink Summary` → 检查 A 检出"章节缺失"型漂移
- `node_wrong_status/`：`trace_status: COMPLETE` 不在 node 五态值域（NOT_STARTED / IN_PROGRESS / DONE_OPEN / DONE_CLOSED / BLOCKED）→ 回归栈间状态值域混淆
- `fullstack_bad_contract/`：契约三桶计数与 `contract_coverage_percent` 不一致（声明 50% ≠ 4/6≈66.7%）→ 回归契约对齐规则
- `fullstack_missing_decl/`：缺分栈完成态声明 → 回归双完成态/四完成态检查
- `fullstack_ok/`：全栈正例，用于确认门禁不误伤合格产物

回归自测命令（基线 2026-09-03 实测）：

```bash
python scripts/validate_audit.py scripts/_demo_audit                        # 根级全样例：PASS=1 FAIL=4 WARN=17，退出码 1
python scripts/validate_audit.py scripts/_demo_audit/dotnet_missing_section  # PASS=4 FAIL=1 WARN=16，退出码 1
python scripts/validate_audit.py scripts/_demo_audit/node_wrong_status       # PASS=4 FAIL=1 WARN=16，退出码 1
python scripts/validate_audit.py scripts/_demo_audit/fullstack_bad_contract  # PASS=5 FAIL=1 WARN=38，退出码 1
python scripts/validate_audit.py scripts/_demo_audit/fullstack_missing_decl  # PASS=5 FAIL=1 WARN=38，退出码 1
python scripts/validate_audit.py scripts/_demo_audit/fullstack_ok            # 正例：FAIL=0，退出码 0
```

## 已知局限（仍需人工 / 模型判断）

- 检查 E 是文本窗口近似匹配，无法把「已确认」精确归因到具体漏洞条目，可能误报
  （如相邻条目共用段落），也可能漏报（条目跨文件拆写）——因此只报 WARN。
- 纯数字短 route_id（如 `1`、`12`）在 vuln_audit 中难以唯一匹配，脚本对其加了
  语境词约束但仍可能漏检。
- 章节标题按「行首 `## N) 标题文本`」前缀匹配；标题被改写（如同义词替换）会判为
  缺失，这正是契约意图，但标题语义等价判断超出脚本能力。
- 字段解析基于 `字段名: 值` / `字段名 = 值` 文本约定；若产物把状态写进无字段名的
  散文句子，脚本无法识别。
- 证据点内容质量（EVID 引用了合法 ID 但证据片段为空 / 不相关）、覆盖率数字真实性、
  「待补证风险池」是否完整等语义判断无法程序化，仍依赖模型自律与人工复核。
