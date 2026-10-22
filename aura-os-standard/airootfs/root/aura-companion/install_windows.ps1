# Aura installer для Windows (PowerShell)
# Требует: Python 3.11+, git, Chocolatey
param(
    [switch]$DryRun
)

Write-Host "=== Aura installer (Windows) ===" -ForegroundColor Cyan
Write-Host "Project: $(Get-Location)"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python не найден. Установи: winget install Python.Python.3.12" -ForegroundColor Red
    exit 1
}

# Проверка Chocolatey
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey не найден. Рекомендую: https://chocolatey.org/install" -ForegroundColor Yellow
}

$packages = @(
    "python",
    "git",
    "ffmpeg"
)

foreach ($pkg in $packages) {
    if ($DryRun) {
        Write-Host "[dry-run] choco install $pkg"
    } else {
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            choco install -y $pkg
        }
    }
}

# venv
if ($DryRun) {
    Write-Host "[dry-run] python -m venv venv"
} else {
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -e .
}

Write-Host ""
Write-Host "=== Готово ===" -ForegroundColor Green
Write-Host "Запусти: python -m aura_main"
