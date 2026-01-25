# PC1 Setup Script for Antigravity (Corrected)
# Run this on PC1 to fix git auth and install RAG environment

$ErrorActionPreference = "Stop"

Write-Host "🚀 INITIALIZING ANTIGRAVITY SETUP FOR PC1" -ForegroundColor Cyan
Write-Host "========================================"

# 1. FIX GIT AUTH
Write-Host "🔐 Fixing Git Authentication..." -ForegroundColor Yellow
git config --global credential.helper manager
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Git Credential Manager enabled." -ForegroundColor Green
}
else {
    Write-Host "   ❌ Failed to set Git Credential Manager." -ForegroundColor Red
}

# 2. LOCATE PROJECT
# Using corrected path for Mr. Schaslivij
$projectPath = "C:\Users\Mr. Schaslivij\.gemini\antigravity\scratch"
if (-not (Test-Path $projectPath)) {
    Write-Host "   ⚠️  Standard path not found: $projectPath" -ForegroundColor Yellow
    $projectPath = Read-Host "   Please enter the full path to your 'scratch' folder"
}

if (Test-Path $projectPath) {
    Set-Location $projectPath
    Write-Host "   📂 Working in: $projectPath" -ForegroundColor Gray
}
else {
    Write-Host "   ❌ Path not found. Exiting." -ForegroundColor Red
    Exit
}

# 3. UPDATE & INSTALL RAG
$ragRepoPath = Join-Path $projectPath "antigravity-rag-memory"
if (Test-Path $ragRepoPath) {
    Write-Host "⬇️  Updating RAG Memory Repo..." -ForegroundColor Yellow
    Set-Location $ragRepoPath
    git pull
    
    Write-Host "📦 Running RAG Installer..." -ForegroundColor Yellow
    .\install_rag.ps1
    
    Write-Host "🧠 Injecting Core Knowledge..." -ForegroundColor Yellow
    python bootstrap_knowledge.py
}
else {
    Write-Host "   ❌ 'antigravity-rag-memory' folder not found in scratch." -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ SETUP COMPLETE." -ForegroundColor Green
Write-Host "You can now run 'Start-Work.ps1' to begin working."
# Removed Read-Host pause for automated execution
# Read-Host "Press Enter to exit..."
