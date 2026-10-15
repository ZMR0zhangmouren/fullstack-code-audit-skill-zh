# node 侧供应链专项判定标准

> node-supply-chain-audit 已交付（ACTIVE，2026-09-04），本文件为其判定标准单一真源。

## 判定标准

1. **确认漏洞**：lockfile 版本命中已知 CVE/GHSA + 依赖在运行时加载路径可达 + 无有效缓解（版本修复/替代包）。
2. **待确认**：CVE 影响版本区间与 locked 版本交集不明、或运行时可达性证据不足 → 降级 `待验证`。
3. **误报**：版本已修复、不可达、或锁定的仅是 devDependencies 且不进入产物 → 输出 `误报` + 判定依据。

## 与工具链的衔接

- 工具输出（npm audit --json / osv-scanner）仅作为初筛证据（EVID_NODE_SUPPLY_TOOL_OUTPUT 预留），可达性判定必须结合 route-trace 与打包产物分析。
- typosquatting/依赖混淆：以 registry 流行度与来源声明为基准，命中标注 `待验证` 并人工复核。
