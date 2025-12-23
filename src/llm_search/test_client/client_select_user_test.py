import asyncio
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 配置服务器启动参数
server_params = StdioServerParameters(
    command=sys.executable,  # 使用当前 Python 解释器
    args=["../mcp-sercer-search/server.py"],  # 你的服务器文件名
    env=None  # 继承当前环境变量
)


async def run_test():
    print("🔌 正在连接 MCP 服务器...")

    # 建立 stdio 连接
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. 初始化会话
            await session.initialize()
            print("✅ 连接成功！")

            # 2. 列出可用工具
            print("\n🔍 正在获取工具列表...")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"   - 工具名: {tool.name}")
                print(f"     描述: {tool.description}")

            # 3. 调用 select_user 工具
            tool_name = "select_user"
            query_args = {"username": "ZhangSan"}

            print(f"\n🚀 正在调用工具: {tool_name}，参数: {query_args}")

            try:
                result = await session.call_tool(tool_name, query_args)

                # 4. 解析并打印结果
                print("\n📦 工具返回结果:")
                # result.content 是一个 TextContent 列表
                for content in result.content:
                    if content.type == "text":
                        print(content.text)
                    else:
                        print(f"[{content.type}] 数据")

            except Exception as e:
                print(f"❌ 调用失败: {e}")


if __name__ == "__main__":
    # 确保 server.py 在同一目录下，或者写绝对路径
    if not os.path.exists("../mcp-sercer-search/server.py"):
        print("错误：在当前目录下未找到 server.py 文件")
    else:
        asyncio.run(run_test())