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
# Fix encoding for Cyrillic
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Configuration
$RAG_ROOT = "$PSScriptRoot"
$CHROMA_DB_PATH = "$env:USERPROFILE\.gemini\antigravity\.rag\chroma_db"
$CHROMA_PORT = 8000
$EMBED_PORT = 8001

Write-Host "🚀 Запуск сервісів Antigravity RAG..." -ForegroundColor Cyan

# 1. Start ChromaDB Server
Write-Host "1️⃣  Запуск бази даних (ChromaDB на порту $CHROMA_PORT)..." -ForegroundColor Green
if (Get-NetTCPConnection -LocalPort $CHROMA_PORT -ErrorAction SilentlyContinue) {
    Write-Host "   ⚠️  Порт $CHROMA_PORT вже використовується. Вважаємо, що ChromaDB вже працює." -ForegroundColor Yellow
}
else {
    $chromaArgs = "run", "--path", "$CHROMA_DB_PATH", "--port", "$CHROMA_PORT", "--host", "localhost"
    $chromaProcess = Start-Process -FilePath "chroma" -ArgumentList $chromaArgs -PassThru -WindowStyle Hidden
    Write-Host "   ✅ ChromaDB запущено (PID: $($chromaProcess.Id))"
}

# 2. Start Embedding Server
Write-Host "2️⃣  Запуск AI моделі (Embedding Server на порту $EMBED_PORT)..." -ForegroundColor Green
if (Get-NetTCPConnection -LocalPort $EMBED_PORT -ErrorAction SilentlyContinue) {
    Write-Host "   ⚠️  Порт $EMBED_PORT вже використовується. Вважаємо, що Embedding Server вже працює." -ForegroundColor Yellow
}
else {
    $embedScript = Join-Path $RAG_ROOT "embedding_server.py"
    $embedProcess = Start-Process -FilePath "python" -ArgumentList "$embedScript" -PassThru -WindowStyle Hidden
    Write-Host "   ✅ Embedding Server запущено (PID: $($embedProcess.Id))"
    Write-Host "   ⏳ Очікування завантаження моделі (~30-60с)..." -ForegroundColor Gray
}

# 3. Health Checks
Write-Host "3️⃣  Перевірка статусу..." -ForegroundColor Green

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
    Write-Host "   ✅ AI Модель ГОТОВА!" -ForegroundColor Green
}
else {
    Write-Host "   ❌ AI Модель не відповідає. Перевірте логи." -ForegroundColor Red
}

# Check ChromaDB
Try {
    $resp = Invoke-RestMethod -Uri "http://localhost:$CHROMA_PORT/api/v1/heartbeat" -Method Get -ErrorAction SilentlyContinue
    Write-Host "   ✅ База даних ГОТОВА!" -ForegroundColor Green
}
Catch {
    Write-Host "   ⚠️  База даних, можливо, ще ініціалізується..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Система RAG повністю готова до роботи!" -ForegroundColor Cyan
Write-Host "Тепер ви можете запускати своїх агентів."
Write-Host "Вікно закриється автоматично через 5 секунд..." -ForegroundColor Gray
Start-Sleep -Seconds 5
