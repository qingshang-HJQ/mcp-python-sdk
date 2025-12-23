import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ErrorData,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)
from mcp.shared.exceptions import McpError
from pydantic import BaseModel, Field, ValidationError
from enum import Enum


# --- 1. 定义工具名称 ---
class PgTools(str, Enum):
    SELECT_USER = "select_user"


# --- 2. 定义输入输出模型 ---

# [修正] 专门为工具定义的入参模型
# 此时只要求输入 username，不需要 id
class SelectUserArgs(BaseModel):
    username: str = Field(..., description="要查询的用户名")


# 输出模型（保持不变）
class OutUser(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool = True
    phone: str


# --- 3. 业务逻辑函数 ---
def select_user(username: str) -> list[OutUser]:
    # 模拟数据库查询
    print(f"正在查询用户: {username}...")
    user_data = {
        "id": 1,
        "username": username,
        "email": "test@example.com",
        "phone": "13800138000"
    }
    return [OutUser(**user_data)]


# --- 4. 服务器实现 ---
async def serve() -> None:
    server = Server("mcp-server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=PgTools.SELECT_USER.value,
                description="根据用户名查询用户信息",
                # 注意：这里使用专门的入参模型，而不是包含 ID 的 User 模型
                inputSchema=SelectUserArgs.model_json_schema(),
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        # 匹配工具名称
        if name == PgTools.SELECT_USER.value:
            try:
                # A. 校验参数：将字典转为 Pydantic 模型
                args = SelectUserArgs(**arguments)

                # B. 执行逻辑：调用具体的 Python 函数
                users = select_user(args.username)

                # C. 格式化结果：将对象列表转为 JSON 字符串
                # model_dump() 将对象转为字典，然后通过 json.dumps 转为字符串
                users_json = json.dumps(
                    [u.model_dump() for u in users],
                    ensure_ascii=False,
                    indent=2
                )

                # D. 返回标准格式：必须是 list[TextContent]
                return [TextContent(type="text", text=users_json)]

            except ValidationError as e:
                # 参数校验失败
                raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
            except Exception as e:
                # 业务逻辑执行失败
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))

        # 如果工具名称无法匹配
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"未找到工具: {name}"))

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)


# 运行入口（如果需要本地测试运行）
if __name__ == "__main__":
    import asyncio

    asyncio.run(serve())