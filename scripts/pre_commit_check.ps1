# pre_commit_check.ps1 — pre-commit 门禁检查入口（T3-13，2026-09-04 用户决策落地）
#
# 调用 scripts/validate_audit.py --stack auto 并透传退出码；不创建 .github/ workflow，
# 是否接入 git hooks 由使用者决定（如：git config core.hooksPath <dir> 后在该目录的
# pre-commit 中调用本脚本，或追加到现有 .git/hooks/pre-commit）。
#
# 用法：
#   .\scripts\pre_commit_check.ps1                        # 默认校验自测样例（回归基线）
#   .\scripts\pre_commit_check.ps1 <audit_output_dir>     # 校验指定审计输出目录
#
# 退出码语义（与 validate_audit.py 一致）：
#   0 = 通过 / 仅 WARN（放行）
#   1 = 存在 FAIL（阻断提交）
#   2 = 用法错误 / 环境缺失

param(
    [string]$Target = "scripts/_demo_audit"
)

$ErrorActionPreference = "Stop"
$repoRoot  = Split-Path -Parent $PSScriptRoot
$validator = Join-Path $PSScriptRoot "validate_audit.py"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "[pre-commit] 未找到 python，请先安装 Python 3.8+"
    exit 2
}
if (-not (Test-Path $validator)) {
    Write-Error "[pre-commit] 未找到门禁脚本: $validator"
    exit 2
}
if (-not (Test-Path (Join-Path $repoRoot $Target))) {
    Write-Error "[pre-commit] 目标目录不存在: $Target"
    exit 2
}

Push-Location $repoRoot
try {
    python $validator $Target --stack auto
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}

# 透传退出码，交由调用方（git hook / CI / 人工）判定
exit $code
