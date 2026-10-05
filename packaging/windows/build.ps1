# Aura Windows — сборка .exe через PyInstaller.
# Наука: PyInstaller spec, Python venv, PowerShell 7.
#
# Запуск: powershell -ExecutionPolicy Bypass -File build.ps1

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Venv = Join-Path $Root ".venv-windows"

Write-Host "[aura-win] Root: $Root"

# 1. Python проверка
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "python не найден. Установи: https://python.org"
}
Write-Host "[aura-win] Python: $(python --version)"

# 2. venv
if (-not (Test-Path $Venv)) {
    Write-Host "[aura-win] Создаю venv..."
    python -m venv $Venv
}
& "$Venv\Scripts\Activate.ps1"

# 3. deps
Write-Host "[aura-win] Устанавливаю зависимости..."
pip install --upgrade pip
pip install pyinstaller
pip install -e $Root

# 4. PyInstaller
Write-Host "[aura-win] Сборка .exe..."
Push-Location $PSScriptRoot
pyinstaller --clean --noconfirm aura.spec
Pop-Location

$out = Join-Path $PSScriptRoot "dist\aura\aura.exe"
if (Test-Path $out) {
    Write-Host "[aura-win] Готово: $out"
    Get-Item $out | Format-List Name, Length, LastWriteTime
} else {
    Write-Error "Сборка не удалась."
}
