<#
.SYNOPSIS
    Installation script for Antigravity RAG Services.
    Can be used to set up the environment on a new machine.

.DESCRIPTION
    This script:
    1. Checks for Python installation.
    2. install dependencies from requirements.txt.
    3. Creates necessary directories.
    4. Provides MCP configuration snippet.

.EXAMPLE
    .\install_rag.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "📦 Installing Antigravity RAG Memory System..." -ForegroundColor Cyan

# 1. Check Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "   ✅ Python found: $pyVersion" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Python NOT found. Please install Python 3.10+ and add to PATH." -ForegroundColor Red
    Exit 1
}

# 2. Install Dependencies
$reqFile = Join-Path $PSScriptRoot "requirements.txt"
if (Test-Path $reqFile) {
    Write-Host "   ⬇️  Installing dependencies..." -ForegroundColor Cyan
    pip install -r $reqFile
}
else {
    Write-Host "   ⚠️  requirements.txt not found!" -ForegroundColor Yellow
}

# 3. Create Directories
$ragDbDir = "$env:USERPROFILE\.gemini\antigravity\.rag\chroma_db"
if (-not (Test-Path $ragDbDir)) {
    New-Item -ItemType Directory -Force -Path $ragDbDir | Out-Null
    Write-Host "   ✅ Created database directory: $ragDbDir" -ForegroundColor Green
}

# 4. Generate MCP Config Snippet
$ragServerPath = Join-Path $PSScriptRoot "server.py"
$ragServerPath = $ragServerPath -replace "\\", "/"  # JSON friendly

Write-Host ""
Write-Host "🎉 Installation Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "👉 ACTION REQUIRED: Add this to your mcp_config.json:" -ForegroundColor Yellow
Write-Host ""
Write-Host """antigravity-rag"": {"
Write-Host "  ""command"": ""python"","
Write-Host "  ""args"": [""$ragServerPath""]"
Write-Host "}"
Write-Host ""
Write-Host "🚀 To start services run: .\start_rag_services.ps1" -ForegroundColor Green
