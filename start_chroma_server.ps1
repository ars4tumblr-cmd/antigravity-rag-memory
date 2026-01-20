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

chroma run --path $CHROMA_PATH --port $CHROMA_PORT --host localhost
