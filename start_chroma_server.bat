@echo off
REM ChromaDB Server Startup Script for Antigravity RAG
REM Run this BEFORE starting Antigravity/VS Code

SET CHROMA_PORT=8000
SET CHROMA_PATH=C:\Users\Mr.Arsist\.gemini\antigravity\.rag\chroma_db

echo Starting ChromaDB server on port %CHROMA_PORT%...
echo Database path: %CHROMA_PATH%
echo.
echo Press Ctrl+C to stop the server
echo.

chroma run --path "%CHROMA_PATH%" --port %CHROMA_PORT% --host localhost
