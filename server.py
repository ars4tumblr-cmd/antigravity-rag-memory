#!/usr/bin/env python3
"""
MCP Server для Antigravity Global RAG Memory.
Забезпечує доступ до векторної бази знань через Model Context Protocol.
"""

import asyncio
import json
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types
from pydantic import Field

# Імпортуємо наш клієнт
from chroma_client import AntigravityRAGClient


# Глобальний інстанс клієнта
rag_client = None


def get_client() -> AntigravityRAGClient:
    """Lazy initialization клієнта ChromaDB."""
    global rag_client
    if rag_client is None:
        rag_client = AntigravityRAGClient()
    return rag_client


# Створюємо MCP сервер
server = Server("antigravity-rag")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Список доступних інструментів."""
    return [
        types.Tool(
            name="store_knowledge",
            description="Зберегти знання в глобальну RAG пам'ять",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Текст для збереження (українська/англійська)"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "ID проекту (наприклад, 'orchestrator_agent')"
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["global", "local", "private"],
                        "default": "local",
                        "description": "Рівень видимості: global (всі), local (проект), private (особисте)"
                    },
                    "entity_type": {
                        "type": "string",
                        "enum": ["preference", "fact", "decision", "code_snippet"],
                        "default": "fact",
                        "description": "Тип знання"
                    },
                    "source_session": {
                        "type": "string",
                        "default": "",
                        "description": "UUID сесії (опціонально)"
                    }
                },
                "required": ["content", "project_id"]
            }
        ),
        types.Tool(
            name="remember_now",
            description="🔥 РУЧНИЙ ТРИГЕР: Миттєво зберегти важливий факт (пріоритет)",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Що запам'ятати"
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["global", "private"],
                        "default": "global",
                        "description": "global = для всіх проектів, private = тільки для мене"
                    },
                    "project_id": {
                        "type": "string",
                        "default": "antigravity",
                        "description": "ID проекту (за замовчуванням 'antigravity')"
                    }
                },
                "required": ["content"]
            }
        ),
        types.Tool(
            name="search_knowledge",
            description="Пошук знань по семантичному запиту",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Запит (українська/англійська)"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "ID проекту для фокусування. Передайте '*' для пошуку по ВСІХ проектах."
                    },
                    "n_results": {
                        "type": "integer",
                        "default": 5,
                        "description": "Кількість результатів"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_project_context",
            description="Отримати контекст проекту для початку сесії",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ID проекту"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Максимальна кількість записів"
                    }
                },
                "required": ["project_id"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Обробка викликів інструментів."""
    
    if not arguments:
        arguments = {}
    
    client = get_client()
    
    try:
        if name == "store_knowledge":
            doc_id = client.store(
                content=arguments["content"],
                project_id=arguments["project_id"],
                scope=arguments.get("scope", "local"),
                entity_type=arguments.get("entity_type", "fact"),
                source_session=arguments.get("source_session", ""),
                manual_save=False
            )
            return [
                types.TextContent(
                    type="text",
                    text=f"✅ Збережено! ID: {doc_id}\nПроект: {arguments['project_id']}\nScope: {arguments.get('scope', 'local')}"
                )
            ]
        
        elif name == "remember_now":
            doc_id = client.store(
                content=arguments["content"],
                project_id=arguments.get("project_id", "antigravity"),
                scope=arguments.get("scope", "global"),
                entity_type="preference",
                manual_save=True  # Пріоритет!
            )
            return [
                types.TextContent(
                    type="text",
                    text=f"🔥 ЗАПАМ'ЯТАНО (пріоритет)!\nID: {doc_id}\nScope: {arguments.get('scope', 'global')}\n\n✨ Цей спогад буде доступний при кожному запуску."
                )
            ]
        
        elif name == "search_knowledge":
            results = client.search(
                query=arguments["query"],
                project_id=arguments.get("project_id"),
                n_results=arguments.get("n_results", 5)
            )
            
            if not results:
                return [types.TextContent(type="text", text="❌ Нічого не знайдено.")]
            
            # Форматуємо результати
            output = f"🔍 Знайдено {len(results)} результатів:\n\n"
            for i, result in enumerate(results, 1):
                meta = result["metadata"]
                output += f"**{i}. [{meta.get('entity_type', 'unknown')}]** (scope: {meta.get('scope', 'unknown')})\n"
                output += f"{result['content'][:200]}{'...' if len(result['content']) > 200 else ''}\n"
                output += f"_Проект: {meta.get('project_id', 'N/A')} | {meta.get('timestamp', 'N/A')}_\n\n"
            
            return [types.TextContent(type="text", text=output)]
        
        elif name == "get_project_context":
            results = client.get_project_context(
                project_id=arguments["project_id"],
                limit=arguments.get("limit", 10)
            )
            
            if not results:
                return [types.TextContent(type="text", text=f"ℹ️ Немає збереженого контексту для проекту '{arguments['project_id']}'.")]
            
            # Форматуємо контекст
            output = f"📦 Контекст проекту '{arguments['project_id']}':\n\n"
            for i, result in enumerate(results, 1):
                meta = result["metadata"]
                priority = "🔥 " if meta.get("manual_save") else ""
                output += f"{priority}**{i}. {meta.get('entity_type', 'fact')}**\n"
                output += f"{result['content'][:150]}{'...' if len(result['content']) > 150 else ''}\n\n"
            
            return [types.TextContent(type="text", text=output)]
        
        else:
            return [types.TextContent(type="text", text=f"❌ Невідомий інструмент: {name}")]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Помилка: {str(e)}")]


async def main():
    """Запуск MCP сервера через stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="antigravity-rag",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
