#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate_audit.py — .NET 白盒安全审计输出目录门禁校验脚本（纯标准库）。

用法:
    python scripts/validate_audit.py <audit_output_dir> [--stack auto|dotnet|node|fullstack]
                                     [--skill-root <path>] [--json]

参数:
    audit_output_dir   一次审计的输出目录（含 route_tracer/ quality/ vuln_audit/ 等阶段目录）
    --stack            审计栈类型（auto: 按输出树探测，默认；dotnet 为既有单栈行为；
                       node 启用检查 N；fullstack 对输出根执行检查 F/F2 并复用双栈 A-F/N）
    --skill-root       skill 库根目录（用于定位 skills/shared/EVIDENCE_POINT_IDS.md 与
                       skills/shared/IO_PATH_CONVENTION.md），默认为脚本所在目录的上一级
    --json             以 JSON 输出机器可读结果（替代人类可读中文报告）

检查项:
    A. trace 契约检查       route_tracer/**/trace_*.md 的 5 个强制章节、trace_status 值域、
                            ## 9) 中 EVID_* ID 合法性（契约: dotnet-route-tracer/SKILL.md）
    B. 占位符残留检查       递归扫描所有 .md，报告未替换的 ${var} / {{var}}
                            （契约: dotnet-audit-pipeline/SKILL.md 完整性约束）
    C. 门禁一致性检查       api_coverage_status / api_coverage_percent / coverage_mode 与
                            pipeline_execution 的冲突（契约: dotnet-audit-pipeline/SKILL.md
                            API Coverage Gate、IO_PATH_CONVENTION.md 覆盖门禁与完成态约定）
    D. 最终报告检查         *代码审计*.md 的双完成态声明、PARTIAL 时 unmapped_routes 存在性、
                            EVID_* ID 合法性（契约: DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md）
    E. 降级语义检查         trace_status=PARTIAL/UNRESOLVED 的 route_id 在 vuln_audit 中
                            被标 ✅已确认 时报 WARN（契约: dotnet-audit-pipeline/SKILL.md 强制约束）
    F. 阶段目录完整性       按 IO_PATH_CONVENTION 检查阶段目录与 index 文件（缺失/空目录报 WARN）

    N. node trace 契约检查   node/route_tracer/**/trace_*.md 的 10 最小章节、trace_status 五态
                            （NOT_STARTED/IN_PROGRESS/DONE_OPEN/DONE_CLOSED/BLOCKED）、EVID 合法性
    F. fullstack 检查       四完成态字段可回溯（dotnet_/node_/contract_ gate 产物）+ 最终报告四声明
                            + cross/contract_coverage_gate 三桶计数与 percent 对齐
                            （--stack=fullstack 时对输出根执行，双栈子目录复用 A-F/N 检查）
    R. 路由计数对账         route_mapping/routes_*.md 头部三字段（declared_route_count /
                            expanded_route_count / count_self_check）与明细实际条数比对；
                            count_self_check=FAIL → FAIL；双字段 unique/method_path_count
                            矛盾 → WARN（契约: DOTNET_ROUTE_OUTPUT_TEMPLATES.md §1.1 /
                            IO_PATH_CONVENTION.md 路由计数双字段口径）
    S. exploit 计数对账     exploit_chain/exploit_chains_*.md 的 consistency_check_counts
                            声明与链路总览表逐行计数比对；最终报告回写
                            exploit_chain_consistency_check_counts 同步对账（不一致 → WARN）
    T. final_anchor 对账    quality/final_anchor_checklist_*.md 汇总计数/判定与最终报告
                            §4.6 回写值逐字段比对（不一致 → WARN）
    U. consistency 归并标记 无独立 coverage_consistency_check_*.md 且 quality/ 全部文件无
                            MERGED_FROM: coverage_consistency_check 标记行 → WARN
                            （P1-8 归并标记格式，契约: DOTNET_ROUTE_OUTPUT_TEMPLATES.md §八）

    注：R/S/T/U 为 P0-1/P0-3 批次新增检查，统一「字段/文件缺失即跳过，不 WARN」保证
    历史产物向后兼容；校验通过时不产生 PASS 记录，保持既有基线汇总稳定。
    V/W 为 B 类（2026-09-18）新增检查，同样缺失即跳过：V 对账最终报告风险池计数与
    pending_pool pool_total；W 探测 vuln_audit/index 的「## 专项派发核对」节存在性。

退出码约定:
    0 = 全部 PASS 或仅存在 WARN
    1 = 存在至少一项 FAIL
    2 = 用法错误或环境错误（目录不存在、EVID 字典不可读等）
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Windows 控制台中文输出兜底
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------- 常量（契约语义，不硬编码行号）

REQUIRED_TRACE_SECTIONS = [
    "## 5) 参数可控性矩阵",
    "## 6) Sink 定位",
    "## 7) Sink Summary",
    "## 8) Trace 完整性声明",
    "## 9) Sink Evidence Type Checklist",
]

TRACE_STATUS_DOMAIN = {"COMPLETE", "PARTIAL", "UNRESOLVED"}

# ---- 栈感知扩展（P0-5）----

NODE_TRACE_SECTIONS = [
    "参数可控性矩阵",
    "Sink 定位",
    "Sink Summary",
    "Trace 完整性声明",
    "Sink Evidence Type Checklist",
]

NODE_TRACE_STATUS_DOMAIN = {"NOT_STARTED", "IN_PROGRESS", "DONE_OPEN", "DONE_CLOSED", "BLOCKED"}


def parse_status_field(text, field):
    """前缀感知完成态字段解析：允许 dotnet_/node_/contract_ 前缀（全栈四声明）。

    修复检查 D 字段名边界误判：`\bapi_coverage_status\b` 无法匹配
    `dotnet_api_coverage_status`（`_` 是单词字符，前缀处无边界）。
    """
    m = re.search(r"(?<![A-Za-z0-9_])(?:(?:dotnet|node|contract)_)?" + re.escape(field)
                  + r"\s*[:：=]\s*\**\s*`?([A-Za-z_]+)", text)
    return m.group(1) if m else None


def detect_stack(audit_dir):
    """auto 探测：输出树含 dotnet/ 与 node/ 子目录 → fullstack；否则按目录名/子结构判 node。"""
    if (audit_dir / "dotnet").is_dir() and (audit_dir / "node").is_dir():
        return "fullstack"
    if (audit_dir / "node").is_dir() or audit_dir.name == "node":
        return "node"
    return "dotnet"


def has_node_section(text, title):
    """node trace 产物章节宽松匹配：行首允许 ## / ### / 数字列表前缀。"""
    pat = re.compile(r"^#{0,3}\s*\d*\.?\s*" + re.escape(title) + r"\b", re.M)
    return pat.search(text) is not None

# 来自 IO_PATH_CONVENTION.md「默认执行模式」与 dotnet-audit-pipeline「输出目录结构」的并集
STAGE_DIRS = [
    "codegraph", "scan_audit", "coverage_audit", "route_mapping", "auth_audit",
    "route_tracer", "briefing", "vuln_audit", "vuln_poc", "framework_audit",
    "cross_analysis", "vuln_report", "exploit_chain", "global_sink_fallback",
    "review", "quality",
]

EVID_TOKEN = re.compile(r"\bEVID_[A-Z0-9_]+\b")

RESULTS = []  # {check, level, message, file, line, fix}


def add(check, level, message, file=None, line=None, fix=None):
    RESULTS.append({
        "check": check, "level": level, "message": message,
        "file": str(file) if file else None, "line": line, "fix": fix,
    })


def read_text(p):
    return p.read_text(encoding="utf-8", errors="replace")


def parse_field(text, field):
    """解析 `field: VALUE` / `field：VALUE` / `field = VALUE` 形式的标量字段。"""
    m = re.search(r"\b" + re.escape(field) + r"\b\s*[:：=]\s*\**\s*`?([A-Za-z_]+)", text)
    return m.group(1) if m else None


def parse_percent(text, field="api_coverage_percent"):
    m = re.search(r"\b" + re.escape(field) + r"\b\s*[:：=]\s*([0-9]+(?:\.[0-9]+)?)\s*%?", text)
    return float(m.group(1)) if m else None


def parse_int_field(text, field):
    """解析整数计数字段（如契约三桶 `matched_count: 3`）。

    parse_field 的值正则 ([A-Za-z_]+) 不支持数字值，纯数字计数须走本函数。
    """
    m = re.search(r"(?<![A-Za-z0-9_])" + re.escape(field)
                  + r"\s*[:：=]\s*([0-9]+)", text)
    return m.group(1) if m else None


def parse_trace_status(text):
    """从 trace 文件解析 trace_status 声明。优先匹配显式赋值形式。"""
    m = re.search(r"\btrace_status\b\s*[:：=]\s*\**\s*`?([A-Z]+)", text)
    if m:
        return m.group(1)
    # 兜底：trace_status 紧邻合法值（容忍表格单元写法 `| trace_status | PARTIAL |`）
    m = re.search(r"\btrace_status\b[^A-Za-z0-9_]{0,8}\b(COMPLETE|PARTIAL|UNRESOLVED)\b", text)
    return m.group(1) if m else None


def has_heading(text, heading):
    """章节标题精确匹配：行首 ## N) 标题文本（允许行尾空白与全角括号补充说明）。"""
    num, title = heading.split(")", 1)
    num = num.lstrip("# ").strip()
    title = title.strip()
    pat = re.compile(r"^##\s+" + re.escape(num) + r"\)\s*" + re.escape(title), re.M)
    return pat.search(text) is not None


def section_slice(text, heading):
    """截取 heading 到下一个同级或更高级标题之间的内容。"""
    idx = text.find(heading)
    if idx < 0:
        return ""
    rest = text[idx + len(heading):]
    m = re.search(r"^##\s", rest, re.M)
    return rest[:m.start()] if m else rest


# ---------------------------------------------------------------- 契约字典加载

def load_evid_ids(skill_root):
    path = Path(skill_root) / "skills" / "shared" / "EVIDENCE_POINT_IDS.md"
    if not path.is_file():
        return None, path
    return set(EVID_TOKEN.findall(read_text(path))), path


# ---------------------------------------------------------------- 检查 A：trace 契约

def check_trace_contract(audit_dir, evid_ids):
    cid = "A_trace契约"
    tracer_dir = audit_dir / "route_tracer"
    traces = []
    if tracer_dir.is_dir():
        traces = sorted(p for p in tracer_dir.rglob("trace_*.md")
                        if not p.name.startswith("trace_summary"))
    if not traces:
        add(cid, "WARN", "未发现 route_tracer/**/trace_*.md，trace 契约检查跳过",
            file=tracer_dir)
        return {}

    route_status = {}  # route_id -> trace_status（供检查 E 使用）
    for p in traces:
        rel = p.relative_to(audit_dir)
        text = read_text(p)
        ok = True

        missing = [h for h in REQUIRED_TRACE_SECTIONS if not has_heading(text, h)]
        if missing:
            ok = False
            add(cid, "FAIL", "trace 文件缺少强制章节: " + "；".join(missing),
                file=rel,
                fix="按 dotnet-route-tracer SKILL.md 单路由报告模板补齐 5 个强制章节"
                    "（## 5) 参数可控性矩阵 / ## 6) Sink 定位 / ## 7) Sink Summary / "
                    "## 8) Trace 完整性声明 / ## 9) Sink Evidence Type Checklist），字段名不得改写")

        status = parse_trace_status(text)
        if status is None:
            ok = False
            add(cid, "FAIL", "无法解析 trace_status 声明", file=rel,
                fix="在 ## 8) Trace 完整性声明 中显式写出 `trace_status: COMPLETE|PARTIAL|UNRESOLVED`")
        elif status not in TRACE_STATUS_DOMAIN:
            ok = False
            add(cid, "FAIL", "trace_status 值非法: %s（合法值域: COMPLETE/PARTIAL/UNRESOLVED）" % status,
                file=rel, fix="将 trace_status 修正为合法值域之一")
        else:
            route_id = p.parent.name
            route_status[route_id] = status

        sec9 = section_slice(text, "## 9) Sink Evidence Type Checklist")
        if sec9 and evid_ids is not None:
            unknown = sorted(set(EVID_TOKEN.findall(sec9)) - evid_ids)
            if unknown:
                ok = False
                add(cid, "FAIL", "## 9) 检查表引用了未登记的 EVID ID: " + ", ".join(unknown),
                    file=rel,
                    fix="EVID_* ID 必须与 skills/shared/EVIDENCE_POINT_IDS.md 原样一致，"
                        "修正拼写或先登记新证据点")

        if ok:
            add(cid, "PASS", "trace 契约通过（章节齐全、trace_status=%s、EVID 引用合法）" % status,
                file=rel)
    return route_status


# ---------------------------------------------------------------- 检查 N：node trace 契约（P0-5）

def check_node_trace_contract(audit_dir, evid_ids):
    cid = "N_node_trace契约"
    tracer_dir = audit_dir / "route_tracer"
    traces = []
    if tracer_dir.is_dir():
        traces = sorted(p for p in tracer_dir.rglob("trace_*.md")
                        if not p.name.startswith("trace_summary"))
    if not traces:
        add(cid, "WARN", "未发现 node/route_tracer/**/trace_*.md，node trace 契约检查跳过",
            file=tracer_dir)
        return {}

    route_status = {}
    for p in traces:
        rel = p.relative_to(audit_dir)
        text = read_text(p)
        ok = True

        missing = [h for h in NODE_TRACE_SECTIONS if not has_node_section(text, h)]
        if missing:
            ok = False
            add(cid, "FAIL", "node trace 文件缺少强制章节: " + "；".join(missing),
                file=rel,
                fix="补齐强制章节（见 node-route-tracer SKILL.md「trace_{timestamp}.md 最小章节」"
                    "的 10 章节定义，其中 5 个最小章节必检：参数可控性矩阵/Sink 定位/"
                    "Sink Summary/Trace 完整性声明/Sink Evidence Type Checklist）")

        # 适配：node 五态含 DONE_OPEN/DONE_CLOSED（下划线值），parse_trace_status 的
        # ([A-Z]+) 值正则无法完整捕获，故用前缀感知的 parse_status_field 解析
        status = parse_status_field(text, "trace_status")
        if status is None:
            ok = False
            add(cid, "FAIL", "无法解析 node trace_status 声明", file=rel,
                fix="在「Trace 完整性声明」中显式写出 `trace_status` 五态之一")
        elif status not in NODE_TRACE_STATUS_DOMAIN:
            ok = False
            add(cid, "FAIL", "node trace_status 值非法: %s（合法值域: %s）"
                % (status, "/".join(sorted(NODE_TRACE_STATUS_DOMAIN))),
                file=rel, fix="修正为 NOT_STARTED/IN_PROGRESS/DONE_OPEN/DONE_CLOSED/BLOCKED")
        else:
            route_status[p.parent.name] = status

        sec = section_slice(text, "Sink Evidence Type Checklist")
        if sec and evid_ids is not None:
            unknown = sorted(set(EVID_TOKEN.findall(sec)) - evid_ids)
            if unknown:
                ok = False
                add(cid, "FAIL", "node checklist 引用了未登记的 EVID ID: " + ", ".join(unknown),
                    file=rel,
                    fix="EVID_* ID 必须与 skills/shared/EVIDENCE_POINT_IDS.md 原样一致")

        if ok:
            add(cid, "PASS", "node trace 契约通过（章节齐全、trace_status=%s、EVID 引用合法）" % status,
                file=rel)
    return route_status


# ---------------------------------------------------------------- 检查 B：占位符残留

PLACEHOLDER_PATTERNS = [
    (re.compile(r"\$\{[^}\n]*\}"), "${var}"),
    (re.compile(r"\{\{[^}\n]*\}\}"), "{{var}}"),
]


def check_placeholders(audit_dir):
    cid = "B_占位符残留"
    md_files = sorted(audit_dir.rglob("*.md"))
    total_findings = 0
    for p in md_files:
        rel = p.relative_to(audit_dir)
        hits = []
        for lineno, line in enumerate(read_text(p).splitlines(), 1):
            for pat, kind in PLACEHOLDER_PATTERNS:
                for m in pat.finditer(line):
                    hits.append((lineno, kind, m.group(0)))
        if hits:
            total_findings += len(hits)
            shown = "; ".join("L%d %s %s" % (ln, kind, tok) for ln, kind, tok in hits[:10])
            more = "（另有 %d 处未列出）" % (len(hits) - 10) if len(hits) > 10 else ""
            add(cid, "FAIL", "发现 %d 处未替换占位符: %s%s" % (len(hits), shown, more),
                file=rel,
                fix="用真实路由/参数替换 ${var} 与 {{var}}；会话字段仅允许单花括号 "
                    "{host}/{cookie}/{token}/{apiKey}/{jwt}")
    if total_findings == 0:
        add(cid, "PASS", "共扫描 %d 个 .md 文件，未发现 ${var}/{{var}} 占位符残留" % len(md_files))


# ---------------------------------------------------------------- 检查 C：门禁一致性

def check_gate_consistency(audit_dir):
    cid = "C_门禁一致性"
    quality = audit_dir / "quality"
    gate_files = sorted(quality.glob("api_coverage_gate_*.md")) if quality.is_dir() else []
    pe_files = sorted(quality.glob("pipeline_execution_*.md")) if quality.is_dir() else []

    if not pe_files:
        add(cid, "WARN", "未发现 quality/pipeline_execution_*.md，门禁一致性检查跳过", file=quality)
        return
    pe = pe_files[-1]
    pe_text = read_text(pe)
    pipeline_execution = parse_field(pe_text, "pipeline_execution")
    if pipeline_execution is None:
        add(cid, "FAIL", "pipeline_execution_*.md 中无法解析 pipeline_execution 字段",
            file=pe.relative_to(audit_dir),
            fix="显式写出 `pipeline_execution: COMPLETED|PARTIAL`")
        return

    gate_status = gate_percent = None
    coverage_mode = parse_field(pe_text, "coverage_mode")
    if gate_files:
        gate = gate_files[-1]
        gate_text = read_text(gate)
        gate_status = parse_status_field(gate_text, "api_coverage_status")
        gate_percent = parse_percent(gate_text)
        coverage_mode = coverage_mode or parse_field(gate_text, "coverage_mode")
    else:
        add(cid, "WARN", "未发现 quality/api_coverage_gate_*.md，只能依据 pipeline_execution 单边校验",
            file=quality)

    if coverage_mode is None:
        coverage_mode = "FULL"  # 契约默认必须为 FULL

    problems = []
    if pipeline_execution == "COMPLETED":
        if coverage_mode == "SAMPLE":
            problems.append("coverage_mode=SAMPLE 时 pipeline_execution 禁止为 COMPLETED")
        if gate_status is not None and gate_status != "COMPLETE":
            problems.append("api_coverage_status=%s 时 pipeline_execution 禁止为 COMPLETED" % gate_status)
        if coverage_mode == "FULL" and gate_percent is not None and gate_percent < 100:
            problems.append("FULL 模式下 api_coverage_percent=%g%% < 100%% 时 "
                            "pipeline_execution 禁止为 COMPLETED" % gate_percent)

    if problems:
        add(cid, "FAIL", "门禁冲突: " + "；".join(problems),
            file=pe.relative_to(audit_dir),
            fix="将 pipeline_execution 降级为 PARTIAL，或先补齐路由映射使 "
                "api_coverage_status=COMPLETE 且 api_coverage_percent=100%")
    else:
        add(cid, "PASS",
            "门禁一致（pipeline_execution=%s, api_coverage_status=%s, percent=%s, coverage_mode=%s）"
            % (pipeline_execution, gate_status, gate_percent, coverage_mode),
            file=pe.relative_to(audit_dir))


# ---------------------------------------------------------------- 检查 D：最终报告

def check_final_report(audit_dir, evid_ids):
    cid = "D_最终报告"
    reports = sorted(audit_dir.rglob("*代码审计*.md"))
    if not reports:
        add(cid, "WARN", "未发现 *代码审计*.md 最终报告，最终报告检查跳过", file=audit_dir)
        return
    p = reports[-1]
    rel = p.relative_to(audit_dir)
    text = read_text(p)
    ok = True

    for field in ("audit_surface_status", "api_coverage_status"):
        if parse_status_field(text, field) is None:
            ok = False
            add(cid, "FAIL", "最终报告缺少完成态声明字段: %s" % field, file=rel,
                fix="按 DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md「1) 完成态双声明」同时声明 "
                    "audit_surface_status 与 api_coverage_status，禁止用单一“已完成”替代")

    coverage_status = parse_status_field(text, "api_coverage_status")
    if coverage_status == "PARTIAL":
        quality = audit_dir / "quality"
        unmapped = list(quality.glob("unmapped_routes_*.md")) if quality.is_dir() else []
        if not unmapped:
            ok = False
            add(cid, "FAIL",
                "api_coverage_status=PARTIAL 但缺少 quality/unmapped_routes_*.md",
                file=rel,
                fix="输出 quality/unmapped_routes_{timestamp}.md（未映射控制器/action/原因/补图建议）")

    if evid_ids is not None:
        unknown = sorted(set(EVID_TOKEN.findall(text)) - evid_ids)
        if unknown:
            ok = False
            add(cid, "FAIL", "最终报告引用了未登记的 EVID ID: " + ", ".join(unknown),
                file=rel,
                fix="EVID_* ID 必须与 skills/shared/EVIDENCE_POINT_IDS.md 原样一致")

    if ok:
        add(cid, "PASS", "最终报告双完成态声明齐全，unmapped_routes 与 EVID 引用合规", file=rel)


# ---------------------------------------------------------------- 检查 E：降级语义

def check_downgrade_semantics(audit_dir, route_status):
    cid = "E_降级语义"
    degraded = {rid: st for rid, st in route_status.items() if st in ("PARTIAL", "UNRESOLVED")}
    if not degraded:
        add(cid, "PASS", "无 trace_status=PARTIAL/UNRESOLVED 的路由，降级语义检查无需执行")
        return
    vuln_dir = audit_dir / "vuln_audit"
    vuln_files = sorted(vuln_dir.glob("*.md")) if vuln_dir.is_dir() else []
    if not vuln_files:
        add(cid, "WARN", "存在降级 trace（%s）但 vuln_audit/ 无产物，无法核对是否被误标已确认"
            % ", ".join(sorted(degraded)), file=vuln_dir)
        return

    hits = 0
    for p in vuln_files:
        rel = p.relative_to(audit_dir)
        lines = read_text(p).splitlines()
        for rid, st in sorted(degraded.items()):
            rid_pat = re.compile(r"(?<![\w\-])" + re.escape(rid) + r"(?![\w\-])")
            hit_lines = []
            for i, line in enumerate(lines):
                if not rid_pat.search(line):
                    continue
                # 纯数字短 ID 易误报：要求同行含路由语境词
                if rid.isdigit() and len(rid) < 3 and not re.search(r"route|路由|入口|endpoint", line, re.I):
                    continue
                window = "\n".join(lines[max(0, i - 2):i + 3])
                if "已确认" in window:
                    hit_lines.append(i + 1)
            if hit_lines:  # 同一 (文件, route_id) 只报一次，避免噪音
                hits += 1
                add(cid, "WARN",
                    "route_id=%s 的 trace_status=%s，但其在漏洞条目标附近出现“已确认”（命中行: %s），"
                    "疑似违反降级语义（精确归因困难，按 WARN 处理）"
                    % (rid, st, ", ".join("L%d" % n for n in hit_lines[:5])),
                    file=rel, line=hit_lines[0],
                    fix="trace_status=PARTIAL/UNRESOLVED 的条目不得标 ✅已确认，"
                        "应降级为 ⚠️待验证 并列入「Trace 未闭合 / 待补证风险池」")
    if hits == 0:
        add(cid, "PASS", "降级路由（%s）未在 vuln_audit 中被标“已确认”"
            % ", ".join(sorted(degraded)))


# ---------------------------------------------------------------- 检查 F：阶段目录完整性

def check_stage_dirs(audit_dir):
    cid = "F_阶段目录完整性"
    missing, warned = 0, 0
    for name in STAGE_DIRS:
        d = audit_dir / name
        if not d.is_dir():
            missing += 1
            add(cid, "WARN", "阶段目录缺失: %s/" % name, file=d,
                fix="按 IO_PATH_CONVENTION 强制落盘模式创建该目录；无产出时写 "
                    "index_{timestamp}.md 或 empty_result_{timestamp}.md 说明原因")
            continue
        files = [f for f in d.rglob("*") if f.is_file()]
        has_index = any(f.name.startswith(("index_", "empty_result_")) for f in files)
        if not files:
            warned += 1
            add(cid, "WARN", "阶段目录为空且无索引文件: %s/" % name, file=d,
                fix="空结果阶段必须落 index_{timestamp}.md 或 empty_result_{timestamp}.md 说明原因")
        elif not has_index:
            warned += 1
            add(cid, "WARN", "阶段目录缺少 index/empty_result 索引文件: %s/（共 %d 个文件）"
                % (name, len(files)), file=d,
                fix="补充 %s/index_{timestamp}.md 记录本阶段执行状态与产物清单" % name)
    if missing == 0 and warned == 0:
        add(cid, "PASS", "全部 %d 个阶段目录存在且均有索引文件" % len(STAGE_DIRS))


# ---------------------------------------------------------------- 检查 F：fullstack 四完成态与契约计数（P0-5）

def check_fullstack_statuses(root):
    cid = "F_fullstack四完成态"
    specs = [
        ("dotnet_api_coverage_status", ["dotnet", "quality", "api_coverage_gate_*.md"], "api_coverage_status"),
        ("node_api_coverage_status", ["node", "quality", "api_coverage_gate_*.md"], "api_coverage_status"),
        ("contract_coverage_status", ["cross", "contract_coverage_gate_*.md"], "contract_coverage_status"),
    ]
    ok = True
    for full_field, rel_parts, inner_field in specs:
        pattern = root.joinpath(*rel_parts)
        files = sorted(pattern.parent.glob(pattern.name)) if pattern.parent.is_dir() else []
        if not files:
            add(cid, "FAIL", "缺少 %s 来源产物: %s" % (full_field, "/".join(rel_parts)),
                file=pattern, fix="四完成态字段必须可回溯到对应 gate 产物")
            ok = False
            continue
        val = parse_status_field(read_text(files[-1]), inner_field)
        if val is None:
            add(cid, "FAIL", "%s 无法解析（%s 中缺 %s 字段）"
                % (full_field, files[-1].relative_to(root), inner_field),
                file=files[-1].relative_to(root),
                fix="按 gate 模板显式写出 %s 字段" % inner_field)
            ok = False

    reports = sorted(root.rglob("*代码审计*.md"))
    if reports:
        text = read_text(reports[-1])
        for field in ("dotnet_api_coverage_status", "node_api_coverage_status",
                      "contract_coverage_status", "audit_surface_status"):
            if parse_status_field(text, field) is None:
                ok = False
                add(cid, "FAIL", "全栈最终报告缺少完成态声明字段: %s" % field,
                    file=reports[-1].relative_to(root),
                    fix="按 FULLSTACK_FINAL_REPORT_FIXED_TEMPLATE 四声明齐全，禁止单一“已完成”替代")
    else:
        add(cid, "WARN", "未发现全栈最终报告 *代码审计*.md，报告四声明检查跳过", file=root)

    if ok:
        add(cid, "PASS", "四完成态字段齐全且可回溯到 gate 产物")
    return ok


def check_contract_gate_counts(cross_dir):
    cid = "F2_contract三桶计数"
    files = sorted(cross_dir.glob("contract_coverage_gate_*.md")) if cross_dir.is_dir() else []
    if not files:
        add(cid, "WARN", "未发现 cross/contract_coverage_gate_*.md，契约计数检查跳过", file=cross_dir)
        return
    p = files[-1]
    text = read_text(p)
    m = parse_int_field(text, "matched_count")
    f = parse_int_field(text, "frontend_only_count")
    b = parse_int_field(text, "backend_only_count")
    pct = parse_percent(text, "contract_coverage_percent")
    if m is None or f is None or b is None:
        add(cid, "FAIL", "contract_coverage_gate 缺少三桶计数字段"
            "（matched_count/frontend_only_count/backend_only_count）",
            file=p.relative_to(cross_dir.parent),
            fix="按 cross-stack-contract-mapper SKILL.md 输出三桶计数与 percent")
        return
    m, f, b = int(m), int(f), int(b)
    total = m + f + b
    if total == 0:
        add(cid, "WARN", "三桶计数全为 0，无法校验 percent", file=p.relative_to(cross_dir.parent))
        return
    expect = m / total * 100
    if pct is None:
        add(cid, "WARN", "contract_coverage_gate 未声明 contract_coverage_percent 字段",
            file=p.relative_to(cross_dir.parent),
            fix="按 cross-stack-contract-mapper SKILL.md 输出 contract_coverage_percent="
                "matched/(matched+frontend_only+backend_only)")
    elif abs(pct - expect) > 0.5:
        add(cid, "FAIL", "contract_coverage_percent=%.1f%% 与三桶计数不符（期望 %.1f%% = matched/total）"
            % (pct, expect), file=p.relative_to(cross_dir.parent),
            fix="contract_coverage_percent 必须等于 matched/(matched+frontend_only+backend_only)")
    else:
        add(cid, "PASS", "contract 三桶计数与 percent 对齐（matched=%d, total=%d）" % (m, total))
    if parse_percent(text, "unnormalized_rate") is None:
        add(cid, "WARN", "contract_coverage_gate 未声明 unnormalized_rate（P1-11 落地后为必填）",
            file=p.relative_to(cross_dir.parent),
            fix="新增 unnormalized_rate=未归一化调用占比，>10%% 强制 PARTIAL")


# ---------------------------------------------------------------- 检查 R/S/T/U：计数对账与归并探测（P0-1/P0-3）

def parse_count_dict(text, field):
    """解析 `{PASS:0, BLOCKED:1, N/A:0}` 形式的计数字典（exploit/final_anchor 对账用）。

    键允许大写字母与斜线（N/A）；返回 {键: int}，字段缺失返回 None。
    """
    m = re.search(re.escape(field) + r"\s*[:：]\s*\{([^{}]*)\}", text)
    if not m:
        return None
    pairs = re.findall(r"\b([A-Z][A-Z/]*)\b\s*[:：]\s*(\d+)", m.group(1))
    return {k: int(v) for k, v in pairs} or None


def _count_diffs(declared, actual):
    """返回 {键: (声明值, 实际值)} 的差异子集；两 dict 均无键时返回 None（无法对账）。"""
    keys = set(declared or {}) | set(actual or {})
    if not keys:
        return None
    return {k: (declared.get(k, 0), actual.get(k, 0)) for k in sorted(keys)
            if declared.get(k, 0) != actual.get(k, 0)}


def _fmt_count_diffs(diffs):
    return "；".join("%s 声明=%d/实际=%d" % (k, d[0], d[1]) for k, d in sorted(diffs.items()))


def check_route_count_reconciliation(audit_dir):
    """R: routes 头部计数三字段与明细实际条数对账（字段缺失即跳过，不 WARN）。"""
    cid = "R_路由计数对账"
    rm_dir = audit_dir / "route_mapping"
    files = sorted(rm_dir.glob("routes_*.md")) if rm_dir.is_dir() else []
    if not files:
        return  # 无 routes 产物 → 跳过
    p = files[-1]
    rel = p.relative_to(audit_dir)
    text = read_text(p)

    declared = parse_int_field(text, "declared_route_count")
    if declared is None:
        return  # 历史产物无三字段头 → 跳过
    expanded = parse_int_field(text, "expanded_route_count")

    # 明细实际条数：优先 `=== [N]` 条目行；无条目行回退「路由清单」节表格数据行
    detail = len(re.findall(r"^===\s*\[\d+\]", text, re.M))
    if detail == 0:
        first_row = True
        for line in section_slice(text, "## 路由清单").splitlines():
            s = line.strip()
            if not s.startswith("|"):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not cells[0] or set(cells[0]) <= set("-: "):
                continue  # 表格分隔行
            if first_row:
                first_row = False  # 表头
                continue
            detail += 1

    if expanded is not None and int(expanded) != detail:
        add(cid, "WARN", "expanded_route_count=%s 与明细实际条数 %d 不一致"
            % (expanded, detail), file=rel,
            fix="按 DOTNET_ROUTE_OUTPUT_TEMPLATES.md §1.1 修正 expanded_route_count，"
                "使其等于 `=== [N]` 条目行（或路由清单表格行）实际条数")
    if expanded is not None and int(declared) != int(expanded):
        add(cid, "WARN", "declared_route_count=%s 与 expanded_route_count=%s 不一致"
            % (declared, expanded), file=rel,
            fix="核对「计数对账」节逐控制器算式，修正声明总数或展开明细，使两值相等")
    self_check = parse_field(text, "count_self_check")
    if self_check == "FAIL":
        add(cid, "FAIL", "count_self_check=FAIL：路由计数自检未通过，禁止交付给下游阶段",
            file=rel,
            fix="回 route-mapper 修正计数对账节（declared/expanded_route_count 与逐控制器算式），"
                "使 count_self_check=PASS 后再进入 route-tracer")

    # 双字段口径：两字段齐备且矛盾（method < unique）才 WARN；缺失不追责（向后兼容）
    unique = parse_int_field(text, "unique_path_count")
    method = parse_int_field(text, "method_path_count")
    if unique is not None and method is not None and int(method) < int(unique):
        add(cid, "WARN", "路由计数双字段口径矛盾: method_path_count=%s < unique_path_count=%s"
            % (method, unique), file=rel,
            fix="按 IO_PATH_CONVENTION.md 路由计数双字段口径修正：(method,path) 展开总数不得小于唯一路径数")


def check_exploit_count_reconciliation(audit_dir):
    """S: exploit 一致性检查计数声明 vs 链路总览表实际条数（缺失即跳过，不 WARN）。

    消费锚点（skills/dotnet-exploit-chain-audit/SKILL.md、DOTNET_ROUTE_OUTPUT_TEMPLATES.md §十）：
    - exploit_chain/exploit_chains_{timestamp}.md「链路总览表」最后一列 consistency_check_status
      逐行计数为实际值；文件内 `consistency_check_counts: {PASS:n, BLOCKED:n, N/A:n}` 为声明值。
    - 最终报告回写 `exploit_chain_consistency_check_counts` 时一并比对。
    """
    cid = "S_exploit计数对账"
    ec_dir = audit_dir / "exploit_chain"
    files = sorted(ec_dir.glob("exploit_chains_*.md")) if ec_dir.is_dir() else []
    if not files:
        return  # 无 exploit_chain 产物 → 跳过
    p = files[-1]
    rel = p.relative_to(audit_dir)
    text = read_text(p)

    tally = {}
    chain_rows = 0
    for line in section_slice(text, "链路总览表").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells[0] or set(cells[0]) <= set("-: ") or "链路编号" in cells[0]:
            continue  # 分隔行 / 表头
        status = cells[-1]
        if status not in ("PASS", "BLOCKED", "N/A"):
            continue  # 老格式总览表无该列 → 无法计数，跳过
        chain_rows += 1
        tally[status] = tally.get(status, 0) + 1

    declared = parse_count_dict(text, "consistency_check_counts")
    if chain_rows and declared is not None:
        diffs = _count_diffs(declared, tally)
        if diffs:
            add(cid, "WARN", "consistency_check_counts 与链路总览表实际计数不一致: %s"
                % _fmt_count_diffs(diffs), file=rel,
                fix="按链路总览表 consistency_check_status 列逐行重新统计并回写 consistency_check_counts")

    reports = sorted(audit_dir.rglob("*代码审计*.md"))
    if reports:
        rp = reports[-1]
        rep = parse_count_dict(read_text(rp), "exploit_chain_consistency_check_counts")
        if chain_rows and rep is not None:
            diffs = _count_diffs(rep, tally)
            if diffs:
                add(cid, "WARN", "最终报告回写 exploit_chain_consistency_check_counts 与链路总览表实际计数不一致: %s"
                    % _fmt_count_diffs(diffs), file=rp.relative_to(audit_dir),
                    fix="重新统计链路总览表并回写最终报告 exploit_chain_consistency_check_counts（先改报告再重跑 quick_validation）")


def check_final_anchor_reconciliation(audit_dir):
    """T: final_anchor_checklist 汇总计数 vs 最终报告 §4.6 回写值（缺失即跳过，不 WARN）。

    消费锚点（DOTNET_ROUTE_OUTPUT_TEMPLATES.md §十一 / DOTNET_FINAL_REPORT_FIXED_TEMPLATE.md §4.6）：
    - checklist 汇总区块: checklist_pass_count / checklist_blocked_count /
      checklist_pending_count / final_anchor_decision；
    - 最终报告 §4.6 回写: final_anchor_decision 与 final_anchor_checklist_counts: {PASS:n, BLOCKED:n, PENDING:n}。
    """
    cid = "T_finalAnchor对账"
    quality = audit_dir / "quality"
    files = sorted(quality.glob("final_anchor_checklist_*.md")) if quality.is_dir() else []
    if not files:
        return  # 无 checklist 产物 → 跳过
    text = read_text(files[-1])
    c_pass = parse_int_field(text, "checklist_pass_count")
    c_blocked = parse_int_field(text, "checklist_blocked_count")
    c_pending = parse_int_field(text, "checklist_pending_count")
    decision = parse_field(text, "final_anchor_decision")
    if decision is None and c_pass is None and c_blocked is None and c_pending is None:
        return  # 汇总区块字段缺失 → 跳过

    reports = sorted(audit_dir.rglob("*代码审计*.md"))
    if not reports:
        return
    rp = reports[-1]
    rel = rp.relative_to(audit_dir)
    rtext = read_text(rp)
    m = re.search(r"^#{2,4}\s*4\.6\)", rtext, re.M)
    sec = rtext[m.start():] if m else rtext  # 无 §4.6 标题时退化为全文（字段名不重叠）
    r_decision = parse_field(sec, "final_anchor_decision")
    r_counts = parse_count_dict(sec, "final_anchor_checklist_counts")
    if r_decision is None and r_counts is None:
        return  # 最终报告未回写 §4.6 → 跳过

    if decision is not None and r_decision is not None and decision != r_decision:
        add(cid, "WARN", "final_anchor_decision 不一致: checklist=%s vs 最终报告§4.6=%s"
            % (decision, r_decision), file=rel,
            fix="按 checklist 汇总区块回写最终报告 §4.6 final_anchor_decision，两者必须逐字段一致")
    if r_counts is not None:
        declared = {"PASS": c_pass, "BLOCKED": c_blocked, "PENDING": c_pending}
        diffs = {k: (r_counts.get(k, 0), int(v)) for k, v in declared.items()
                 if v is not None and r_counts.get(k, 0) != int(v)}
        if diffs:
            add(cid, "WARN", "final_anchor_checklist_counts 与 checklist 汇总计数不一致: %s"
                % _fmt_count_diffs(diffs), file=rel,
                fix="按 quality/final_anchor_checklist_*.md 汇总区块回写最终报告 §4.6 "
                    "final_anchor_checklist_counts={{PASS, BLOCKED, PENDING}}")


def check_consistency_merge_marker(audit_dir):
    """U: coverage_consistency_check 独立产物 / 归并标记探测（P1-8）。

    契约（DOTNET_ROUTE_OUTPUT_TEMPLATES.md §八 双栈同构（强制））：无独立
    coverage_consistency_check_*.md 时，归并文件必须含标记行
    `MERGED_FROM: coverage_consistency_check_{timestamp}.md`；两者皆无视为产物缺失。
    """
    cid = "U_consistency归并标记"
    quality = audit_dir / "quality"
    if not quality.is_dir():
        return
    if any(quality.glob("coverage_consistency_check_*.md")):
        return  # 独立文件存在 → 通过（不产生记录，保持基线汇总稳定）
    for f in sorted(quality.rglob("*.md")):
        if "MERGED_FROM: coverage_consistency_check" in read_text(f):
            return  # 归并标记存在 → 通过
    add(cid, "WARN", "quality/ 无独立 coverage_consistency_check_*.md，且全部 quality 文件均无 "
        "MERGED_FROM: coverage_consistency_check 归并标记行（P1-8 归并标记格式），视为产物缺失",
        file=quality,
        fix="按 DOTNET_ROUTE_OUTPUT_TEMPLATES.md §八 落盘独立 coverage_consistency_check_{timestamp}.md；"
            "如确需归并，须在归并文件加入标记行 MERGED_FROM: coverage_consistency_check_{timestamp}.md "
            "与 MERGE_REASON: {归并原因}，且被归并路径仍须在 manifest 登记")


# ---------------------------------------------------------------- 检查 V/W：pending_pool 对账与派发核对（P1-7）

def check_pending_pool_reconciliation(audit_dir):
    """V: pending_pool 单一真源 pool_total vs 最终报告风险池计数（缺失即跳过，不 WARN）。

    契约（IO_PATH_CONVENTION.md「待补证风险池单一真源（2026-09-18）」/ spec §4.2-§4.3）：
    - 单一真源 quality/pending_pool_{timestamp}.md 头部必含 `pool_total: {N}`；
    - 最终报告「Trace 未闭合 / 待补证风险池」节只引用 pending_pool 计数与路径。
    最终报告侧计数依次尝试 pending_pool_count / pool_total / risk_pool_total，
    三者均无则跳过（历史产物不追责）。
    """
    cid = "V_pendingPool对账"
    quality = audit_dir / "quality"
    pool_files = sorted(quality.glob("pending_pool_*.md")) if quality.is_dir() else []
    if not pool_files:
        return  # 无 pending_pool 真源产物 → 跳过
    total = parse_int_field(read_text(pool_files[-1]), "pool_total")
    if total is None:
        return  # 真源头字段缺失 → 跳过

    reports = sorted(audit_dir.rglob("*代码审计*.md"))
    if not reports:
        return
    rp = reports[-1]
    rel = rp.relative_to(audit_dir)
    rtext = read_text(rp)
    rep_total = None
    for field in ("pending_pool_count", "pool_total", "risk_pool_total"):
        v = parse_int_field(rtext, field)
        if v is not None:
            rep_total = int(v)
            break
    if rep_total is None:
        return  # 最终报告未引用风险池计数 → 跳过

    if rep_total != int(total):
        add(cid, "WARN",
            "最终报告风险池计数=%d 与 pending_pool pool_total=%d 不一致"
            % (rep_total, int(total)), file=rel,
            fix="按 quality/pending_pool_{timestamp}.md 的 pool_total 回写最终报告风险池节，"
                "最终报告只引用 pending_pool 计数与路径（IO_PATH_CONVENTION.md 待补证风险池单一真源）")


def check_dispatch_roster(audit_dir):
    """W: vuln_audit/index 专项派发核对节存在性（index 缺失即跳过，不 WARN）。

    契约（IO_PATH_CONVENTION.md 漏洞专项状态模型节 / spec §7）：漏洞 index
    （vuln_audit/index_{timestamp}.md）必须含「## 专项派发核对」节，
    PHASE_STATUS 全部 ACTIVE 专项逐一对勾（触发/否定证据/不适用 三态）。
    本检查只做「核对节存在性」；ACTIVE 专项数与核对行数对账暂未实现
    （PHASE_STATUS 表解析留待后续轮次），在 docstring 注明。
    """
    cid = "W_派发核对"
    va_dir = audit_dir / "vuln_audit"
    files = sorted(va_dir.glob("index_*.md")) if va_dir.is_dir() else []
    if not files:
        return  # 无 vuln_audit/index 产物 → 跳过
    for p in files:
        if "## 专项派发核对" in read_text(p):
            continue
        add(cid, "WARN", "vuln_audit/index 缺少「## 专项派发核对」节",
            file=p.relative_to(audit_dir),
            fix="按 IO_PATH_CONVENTION.md 漏洞专项状态模型节补「## 专项派发核对」节："
                "PHASE_STATUS 全部 ACTIVE 专项逐一对勾（触发/否定证据/不适用 三态），"
                "禁止裸「未触发」「未执行」字样")


# ---------------------------------------------------------------- 报告与入口

def print_human_report(audit_dir):
    level_mark = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}
    print("=" * 72)
    print(".NET 审计输出门禁校验报告")
    print("审计输出目录: %s" % audit_dir)
    print("=" * 72)
    current = None
    for r in RESULTS:
        if r["check"] != current:
            current = r["check"]
            print("\n■ 检查 %s" % current)
        loc = ""
        if r["file"]:
            loc = "  @ %s" % r["file"]
            if r["line"]:
                loc += ":%d" % r["line"]
        print("  %s %s%s" % (level_mark[r["level"]], r["message"], loc))
        if r["level"] == "FAIL" and r["fix"]:
            print("         修复建议: %s" % r["fix"])

    counts = {lv: sum(1 for r in RESULTS if r["level"] == lv) for lv in ("PASS", "FAIL", "WARN")}
    print("\n" + "-" * 72)
    print("汇总: PASS=%d  FAIL=%d  WARN=%d" % (counts["PASS"], counts["FAIL"], counts["WARN"]))
    verdict = "存在 FAIL，门禁未通过" if counts["FAIL"] else "无 FAIL（WARN 不阻断交付，但需复核）"
    print("结论: %s" % verdict)
    print("-" * 72)
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=".NET 白盒安全审计输出目录门禁校验（trace 契约/占位符/门禁一致性/最终报告/降级语义/阶段目录）")
    ap.add_argument("audit_output_dir", help="一次审计的输出目录")
    ap.add_argument("--stack", default="auto", choices=["auto", "dotnet", "node", "fullstack"],
                    help="审计栈类型（auto: 按输出树探测；dotnet 为既有单栈行为）")
    ap.add_argument("--skill-root", default=None,
                    help="skill 库根目录（默认: 脚本所在目录的上一级）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args(argv)

    audit_dir = Path(args.audit_output_dir)
    if not audit_dir.is_dir():
        print("错误: 审计输出目录不存在或不是目录: %s" % audit_dir, file=sys.stderr)
        return 2

    skill_root = Path(args.skill_root) if args.skill_root else Path(__file__).resolve().parent.parent
    evid_ids, evid_path = load_evid_ids(skill_root)
    if evid_ids is None:
        print("错误: 无法读取 EVID 字典: %s（可用 --skill-root 指定 skill 库根目录）" % evid_path,
              file=sys.stderr)
        return 2

    stack = args.stack if args.stack != "auto" else detect_stack(audit_dir)
    if stack == "fullstack":
        dotnet_dir = audit_dir / "dotnet"
        node_dir = audit_dir / "node"
        if dotnet_dir.is_dir():
            route_status = check_trace_contract(dotnet_dir, evid_ids)
            check_placeholders(dotnet_dir)
            check_gate_consistency(dotnet_dir)
            check_final_report(dotnet_dir, evid_ids)
            check_downgrade_semantics(dotnet_dir, route_status)
            check_stage_dirs(dotnet_dir)
            check_route_count_reconciliation(dotnet_dir)
            check_exploit_count_reconciliation(dotnet_dir)
            check_final_anchor_reconciliation(dotnet_dir)
            check_consistency_merge_marker(dotnet_dir)
            check_pending_pool_reconciliation(dotnet_dir)
            check_dispatch_roster(dotnet_dir)
        else:
            add("F_fullstack四完成态", "WARN", "fullstack 输出树缺少 dotnet/ 子树",
                file=dotnet_dir)
        if node_dir.is_dir():
            check_node_trace_contract(node_dir, evid_ids)
            check_placeholders(node_dir)
            check_gate_consistency(node_dir)
            check_final_report(node_dir, evid_ids)
            check_stage_dirs(node_dir)
            check_route_count_reconciliation(node_dir)
            check_exploit_count_reconciliation(node_dir)
            check_final_anchor_reconciliation(node_dir)
            check_consistency_merge_marker(node_dir)
            check_pending_pool_reconciliation(node_dir)
            check_dispatch_roster(node_dir)
        else:
            add("F_fullstack四完成态", "WARN", "fullstack 输出树缺少 node/ 子树",
                file=node_dir)
        check_fullstack_statuses(audit_dir)
        check_contract_gate_counts(audit_dir / "cross")
        check_exploit_count_reconciliation(audit_dir / "cross")
        check_placeholders(audit_dir / "cross")
    elif stack == "node":
        check_node_trace_contract(audit_dir, evid_ids)
        check_placeholders(audit_dir)
        check_gate_consistency(audit_dir)
        check_final_report(audit_dir, evid_ids)
        check_stage_dirs(audit_dir)
        check_route_count_reconciliation(audit_dir)
        check_exploit_count_reconciliation(audit_dir)
        check_final_anchor_reconciliation(audit_dir)
        check_consistency_merge_marker(audit_dir)
        check_pending_pool_reconciliation(audit_dir)
        check_dispatch_roster(audit_dir)
    else:  # dotnet（既有行为，回归保持）
        route_status = check_trace_contract(audit_dir, evid_ids)
        check_placeholders(audit_dir)
        check_gate_consistency(audit_dir)
        check_final_report(audit_dir, evid_ids)
        check_downgrade_semantics(audit_dir, route_status)
        check_stage_dirs(audit_dir)
        check_route_count_reconciliation(audit_dir)
        check_exploit_count_reconciliation(audit_dir)
        check_final_anchor_reconciliation(audit_dir)
        check_consistency_merge_marker(audit_dir)
        check_pending_pool_reconciliation(audit_dir)
        check_dispatch_roster(audit_dir)

    counts = {lv: sum(1 for r in RESULTS if r["level"] == lv) for lv in ("PASS", "FAIL", "WARN")}
    exit_code = 1 if counts["FAIL"] else 0

    if args.json:
        print(json.dumps({
            "audit_dir": str(audit_dir),
            "stack": stack,
            "skill_root": str(skill_root),
            "evid_dict": str(evid_path),
            "summary": counts,
            "exit_code": exit_code,
            "results": RESULTS,
        }, ensure_ascii=False, indent=2))
    else:
        print_human_report(audit_dir)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
