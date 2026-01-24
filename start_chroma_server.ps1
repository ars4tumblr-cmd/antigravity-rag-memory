#!/usr/bin/env pwsh
# ChromaDB Server Startup Script for Antigravity RAG
# Run this BEFORE starting Antigravity/VS Code

$CHROMA_PORT = 8000
$CHROMA_PATH = "$env:USERPROFILE\.gemini\antigravity\.rag\chroma_db"

Write-Host "Starting ChromaDB server on port $CHROMA_PORT..." -ForegroundColor Cyan
Write-Host "Database path: $CHROMA_PATH" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

$VENV_PYTHON = "$PSScriptRoot\.venv\Scripts\python.exe"

if (Test-Path $VENV_PYTHON) {
    # Use venv python to run chroma
    # Need to run module chromadb.cli.main or similar? 
    # Actually just simple 'chroma' command is a script in Scripts folder.
    $CHROMA_EXE = "$PSScriptRoot\.venv\Scripts\chroma.exe"
    & $CHROMA_EXE run --path $CHROMA_PATH --port $CHROMA_PORT --host localhost
} else {
    # Fallback to system chroma if venv missing (legacy support)
    chroma run --path $CHROMA_PATH --port $CHROMA_PORT --host localhost
}

