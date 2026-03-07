# -*- coding:utf-8 -*-
"""
知乎收藏夹导出工具 - MCP Server
将知乎收藏夹导出功能封装为MCP服务，供AI Agent调用
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# 确保可以导入main模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# 导入main模块的功能
import main

# 创建MCP服务器实例
app = Server("zhihu-collections")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="list_collections",
            description="列出配置文件中所有知乎收藏夹",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="export_collection",
            description="导出指定知乎收藏夹为Markdown文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection_url": {
                        "type": "string",
                        "description": "收藏夹URL，如 https://www.zhihu.com/collection/123456789"
                    },
                    "collection_name": {
                        "type": "string",
                        "description": "收藏夹名称（可选，用于命名输出目录）"
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "输出目录路径（可选，默认为downloads）"
                    }
                },
                "required": ["collection_url"]
            }
        ),
        Tool(
            name="get_collection_info",
            description="获取指定收藏夹的基本信息（文章数量等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "collection_url": {
                        "type": "string",
                        "description": "收藏夹URL"
                    }
                },
                "required": ["collection_url"]
            }
        ),
        Tool(
            name="search_collections",
            description="在配置文件中搜索包含关键词的收藏夹",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["keyword"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """处理工具调用"""
    try:
        if name == "list_collections":
            return await list_collections_handler()
        elif name == "export_collection":
            return await export_collection_handler(arguments)
        elif name == "get_collection_info":
            return await get_collection_info_handler(arguments)
        elif name == "search_collections":
            return await search_collections_handler(arguments)
        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}\n{traceback.format_exc()}")]


async def list_collections_handler() -> list[TextContent]:
    """处理list_collections工具调用"""
    config = main.load_config()
    collections = config.get("zhihuUrls", [])

    if not collections:
        return [TextContent(type="text", text="未找到配置的收藏夹，请在config.json中添加收藏夹信息")]

    result = "📚 已配置的收藏夹列表：\n\n"
    for i, coll in enumerate(collections, 1):
        name = coll.get("name", "未命名")
        url = coll.get("url", "")
        result += f"{i}. **{name}**\n"
        result += f"   URL: {url}\n\n"

    return [TextContent(type="text", text=result)]


async def export_collection_handler(args: dict) -> list[TextContent]:
    """处理export_collection工具调用"""
    collection_url = args.get("collection_url")
    collection_name = args.get("collection_name", "")
    output_dir = args.get("output_dir", "")

    if not collection_url:
        return [TextContent(type="text", text="错误: 需要提供collection_url参数")]

    # 如果没有提供名称，从URL中提取
    if not collection_name:
        collection_id = collection_url.split('?')[0].split('/')[-1]
        collection_name = f"收藏夹_{collection_id}"

    # 解析输出路径
    output_path = None
    if output_dir:
        config = main.load_config()
        os_type = config.get("os", "")
        output_path = main.parse_output_path(output_dir, os_type)

    # 设置输出路径
    if output_path:
        original_output = main.parse_output_path(config.get("outputPath", ""), config.get("os", ""))
        main.OUTPUT_PATH = str(output_path)
    else:
        main.OUTPUT_PATH = main.get_output_path(collection_name)

    result = f"🚀 开始导出收藏夹：{collection_name}\n"
    result += f"📎 URL: {collection_url}\n"
    result += f"📁 输出目录: {main.OUTPUT_PATH}\n\n"

    # 执行导出
    try:
        main.process_single_collection(collection_name, collection_url)
        result += "✅ 导出完成！"
    except Exception as e:
        result += f"❌ 导出失败: {str(e)}"

    return [TextContent(type="text", text=result)]


async def get_collection_info_handler(args: dict) -> list[TextContent]:
    """处理get_collection_info工具调用"""
    collection_url = args.get("collection_url")

    if not collection_url:
        return [TextContent(type="text", text="错误: 需要提供collection_url参数")]

    try:
        collection_id = collection_url.split('?')[0].split('/')[-1]
        urls, titles = main.get_article_urls_in_collection(collection_id)

        result = f"📊 收藏夹信息\n\n"
        result += f"🆔 收藏夹ID: {collection_id}\n"
        result += f"📝 文章数量: {len(urls)}\n"

        if titles:
            result += f"\n📄 文章标题（前5个）：\n"
            for i, title in enumerate(titles[:5], 1):
                result += f"  {i}. {title}\n"
            if len(titles) > 5:
                result += f"  ... 还有 {len(titles) - 5} 篇"

        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"获取收藏夹信息失败: {str(e)}")]


async def search_collections_handler(args: dict) -> list[TextContent]:
    """处理search_collections工具调用"""
    keyword = args.get("keyword", "")

    if not keyword:
        return [TextContent(type="text", text="错误: 需要提供keyword参数")]

    config = main.load_config()
    collections = config.get("zhihuUrls", [])

    if not collections:
        return [TextContent(type="text", text="未找到配置的收藏夹")]

    # 搜索匹配的收藏夹
    matched = []
    for coll in collections:
        name = coll.get("name", "")
        url = coll.get("url", "")
        if keyword.lower() in name.lower() or keyword.lower() in url.lower():
            matched.append(coll)

    if not matched:
        return [TextContent(type="text", text=f"没有找到包含 '{keyword}' 的收藏夹")]

    result = f"🔍 搜索结果（关键词：{keyword}）：\n\n"
    for i, coll in enumerate(matched, 1):
        name = coll.get("name", "未命名")
        url = coll.get("url", "")
        result += f"{i}. **{name}**\n"
        result += f"   URL: {url}\n\n"

    return [TextContent(type="text", text=result)]


async def main():
    """MCP服务器主入口"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import traceback
    asyncio.run(main())