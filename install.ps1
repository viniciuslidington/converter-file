# install.ps1 — Windows (PowerShell)
# Requer winget (Windows 10/11 com App Installer) e permissao de administrador.

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==> Instalando converter-file..." -ForegroundColor Cyan

# Python 3.11
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "==> Instalando Python 3.11..."
    winget install --id Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements
    # Recarrega PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
} else {
    Write-Host "v Python ja instalado"
}

# ffmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "==> Instalando ffmpeg..."
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
} else {
    Write-Host "v ffmpeg ja instalado"
}

# Pacote Python
Write-Host "==> Instalando pacote converter-file..."
python -m pip install -e $ScriptDir -q

Write-Host ""
Write-Host "v Instalacao concluida!" -ForegroundColor Green
Write-Host ""
Write-Host "  Use o comando:  convert-file"
Write-Host ""
Write-Host "  Se o comando nao for encontrado, reinicie o terminal."
