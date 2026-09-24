# KYLA local low-credit setup (Windows 11 / PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> KYLA local setup (no cloud API keys required)"

if (-not (Test-Path .venv)) {
  py -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "==> Checking system tools"
function Has-Cmd($name) { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }

if (-not (Has-Cmd "ffmpeg")) {
  Write-Host "    Install ffmpeg: winget install Gyan.FFmpeg   (or choco install ffmpeg)"
} else { Write-Host "    ffmpeg OK" }

pip install -q "yt-dlp>=2024.1"
if ($env:KYLA_INSTALL_CLIP -ne "0") {
  Write-Host "==> Installing optional clip deps"
  pip install -r requirements-clip.txt
  pip install -q auto-editor
}

$Model = if ($env:KYLA_OLLAMA_MODEL) { $env:KYLA_OLLAMA_MODEL } else { "qwen2.5:3b" }
Write-Host "==> Ollama (local LLM — zero credits)"
if (Has-Cmd "ollama") {
  Write-Host "    ollama found — pull with: ollama pull $Model"
  Write-Host "    Alt 8GB model: ollama pull phi4-mini"
} else {
  Write-Host "    Install from https://ollama.com/download (Windows installer)"
  Write-Host "    Then: ollama pull $Model"
}

$ClipDir = Join-Path (Split-Path $Root -Parent) "kyla-clip"
if (Test-Path (Join-Path $ClipDir "src\kyla_clip")) {
  Write-Host "==> Linking sibling kyla-clip"
  pip install -e $ClipDir
}

New-Item -ItemType Directory -Force -Path outputs\clips | Out-Null
Write-Host ""
Write-Host "Done. Next:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  ollama serve   # if not already running as a service"
Write-Host "  ollama pull $Model"
Write-Host "  python main.py --dry-run `"hello`""
Write-Host "  python main.py --agent ollama --execute `"summarize my day in 3 bullets`""
Write-Host "  python tools/clip_agent.py --help"
