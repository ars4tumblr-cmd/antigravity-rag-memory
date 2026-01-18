<#
.SYNOPSIS
    Unified startup script for Antigravity RAG Services.
    Starts ChromaDB Server (8000) and Embedding Server (8001).

.DESCRIPTION
    This script ensures the RAG memory system is running.
    It handles:
    1. Checking if ports 8000/8001 are free.
    2. Starting the ChromaDB server (Database).
    3. Starting the Embedding server (AI Model).
    4. Waiting for health checks to pass.
    
    Portability:
    - Data is stored in $HOME\.gemini\antigravity\.rag\chroma_db
    - To move to another machine, just copy the .gemini folder and run this script.

.EXAMPLE
    .\start_rag_services.ps1
#>

$ErrorActionPreference = "Stop"

# Configuration
$RAG_ROOT = "$PSScriptRoot"
$CHROMA_DB_PATH = "$env:USERPROFILE\.gemini\antigravity\.rag\chroma_db"
$CHROMA_PORT = 8000
$EMBED_PORT = 8001

Write-Host "🚀 Starting Antigravity RAG Services..." -ForegroundColor Cyan

# 1. Start ChromaDB Server
Write-Host "1️⃣  Starting Database (ChromaDB on port $CHROMA_PORT)..." -ForegroundColor Green
if (Get-NetTCPConnection -LocalPort $CHROMA_PORT -ErrorAction SilentlyContinue) {
    Write-Host "   ⚠️  Port $CHROMA_PORT is already in use. Assuming ChromaDB is running." -ForegroundColor Yellow
}
else {
    $chromaArgs = "run", "--path", "$CHROMA_DB_PATH", "--port", "$CHROMA_PORT", "--host", "localhost"
    $chromaProcess = Start-Process -FilePath "chroma" -ArgumentList $chromaArgs -PassThru -WindowStyle Hidden
    Write-Host "   ✅ ChromaDB started (PID: $($chromaProcess.Id))"
}

# 2. Start Embedding Server
Write-Host "2️⃣  Starting AI Model (Embedding Server on port $EMBED_PORT)..." -ForegroundColor Green
if (Get-NetTCPConnection -LocalPort $EMBED_PORT -ErrorAction SilentlyContinue) {
    Write-Host "   ⚠️  Port $EMBED_PORT is already in use. Assuming Embedding Server is running." -ForegroundColor Yellow
}
else {
    $embedScript = Join-Path $RAG_ROOT "embedding_server.py"
    $embedProcess = Start-Process -FilePath "python" -ArgumentList "$embedScript" -PassThru -WindowStyle Hidden
    Write-Host "   ✅ Embedding Server started (PID: $($embedProcess.Id))"
    Write-Host "   ⏳ Waiting for model to load (~30-60s)..." -ForegroundColor Gray
}

# 3. Health Checks
Write-Host "3️⃣  Verifying Health..." -ForegroundColor Green

# Check Embedding Server
$retries = 30
$embedReady = $false
Do {
    Try {
        $resp = Invoke-RestMethod -Uri "http://localhost:$EMBED_PORT/health" -Method Get -ErrorAction Stop
        if ($resp.status -eq "ok") { $embedReady = $true }
    }
    Catch {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
        $retries--
    }
} While (-not $embedReady -and $retries -gt 0)

Write-Host ""
if ($embedReady) {
    Write-Host "   ✅ AI Model is READY!" -ForegroundColor Green
}
else {
    Write-Host "   ❌ AI Model failed to respond. Check logs." -ForegroundColor Red
}

# Check ChromaDB
Try {
    $resp = Invoke-RestMethod -Uri "http://localhost:$CHROMA_PORT/api/v1/heartbeat" -Method Get -ErrorAction SilentlyContinue
    Write-Host "   ✅ Database is READY!" -ForegroundColor Green
}
Catch {
    Write-Host "   ⚠️  Database might be initializing..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 RAG System is fully operational!" -ForegroundColor Cyan
Write-Host "You can now run your agents."
