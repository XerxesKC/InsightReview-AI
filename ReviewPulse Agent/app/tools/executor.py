import yaml
import logging
from pathlib import Path
from app.rag.llm import get_llm

from app.tools.merchant_tools import (
    execute_get_merchant_top_liked_post,
    execute_get_merchant_latest_comments,
    execute_get_merchant_negative_comments
)

from app.tools.user_tools import (
    execute_get_user_latest_comments,
    execute_summarize_merchant_comments,
    execute_search_merchants,
    execute_get_user_bookmarks
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
MERCHANT_TOOLS_YAML = BASE_DIR / "merchant_tools.yaml"
USER_TOOLS_YAML = BASE_DIR / "user_tools.yaml"


def load_tools_from_yaml(yaml_path: Path):
    """通用工具加载方法"""
    if not yaml_path.exists():
        return []

    with open(yaml_path, "r", encoding="utf-8") as f:
        tools_config = yaml.safe_load(f)

    formatted_tools = []
    if tools_config:
        for tool in tools_config:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get("args_schema", {"type": "object", "properties": {}})
                }
            })
    return formatted_tools

MERCHANT_TOOLS = load_tools_from_yaml(MERCHANT_TOOLS_YAML)
USER_TOOLS = load_tools_from_yaml(USER_TOOLS_YAML)

async def process_tool_use_intent(query: str, user: dict, session, model_name: str) -> list:

    llm = get_llm(model_name=model_name)
    user_type = user.get("user_type", "user")
    available_tools = MERCHANT_TOOLS if user_type == "merchant" else USER_TOOLS

    if not available_tools:
        return [
            ("system", "你是一个专业友好的数据查询助手。"),
            ("user", f"【系统提示】当前角色({user_type})暂无对应的数据查询工具可用。\n\n我的问题是：{query}")
        ]

    llm_with_tools = llm.bind_tools(available_tools)
    tool_call_messages = [
        ("system",
         f"你是一个智能工具路由引擎。当前提问者的身份是【{'商家' if user_type == 'merchant' else '普通用户'}】。请根据用户的需求，选择并调用正确的工具来解答。"),
        ("user", query)
    ]

    tool_context = "【系统提示】正在调用工具，但未获取到结果。"

    try:
        ai_msg = await llm_with_tools.ainvoke(tool_call_messages)

        if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
            tool_call = ai_msg.tool_calls[0]
            tool_name = tool_call["name"]
            args = tool_call["args"]

            if user_type == "merchant":
                if tool_name == "get_merchant_top_liked_post":
                    m_id = args.get("merchant_id") or user.get("user_id")
                    db_result = await execute_get_merchant_top_liked_post(session, m_id)
                    tool_context = f"【执行结果】\n{db_result}"

                elif tool_name == "get_merchant_latest_comments":
                    m_id = args.get("merchant_id") or user.get("user_id")
                    limit = args.get("limit", 3)
                    db_result = await execute_get_merchant_latest_comments(session, m_id, limit)
                    tool_context = f"【执行结果】\n{db_result}"

                elif tool_name == "get_merchant_negative_comments":
                    m_id = args.get("merchant_id") or user.get("user_id")
                    limit = args.get("limit", 3)
                    db_result = await execute_get_merchant_negative_comments(session, m_id, limit)
                    tool_context = f"【执行结果】\n{db_result}"

            elif user_type == "user":
                if tool_name == "get_user_latest_comments":
                    u_id = args.get("user_id") or user.get("user_id")
                    limit = args.get("limit", 3)
                    db_result = await execute_get_user_latest_comments(session, u_id, limit)
                    tool_context = f"【执行结果】\n{db_result}"
                elif tool_name == "summarize_merchant_comments":
                    merchant_name = args.get("merchant_name")
                    if merchant_name:
                        db_result = await execute_summarize_merchant_comments(session, merchant_name)
                        tool_context = f"【执行结果】\n{db_result}"
                    else:
                        tool_context = "【系统提示】大模型未能提取到具体的商家名称，请引导用户提供要查询的商家名。"
                elif tool_name == "search_merchants":
                    keyword = args.get("keyword", "")
                    min_rating = args.get("min_rating", 0.0)
                    max_price = args.get("max_price", 9999.0)
                    db_result = await execute_search_merchants(session, keyword, min_rating, max_price)
                    tool_context = f"【执行结果】\n{db_result}"
                elif tool_name == "get_user_bookmarks":
                    u_id = args.get("user_id") or user.get("user_id")
                    db_result = await execute_get_user_bookmarks(session, u_id)
                    tool_context = f"【执行结果】\n{db_result}"
        else:
            tool_context = "【系统提示】未能匹配到合适的工具，请尝试基于常识回答。"

    except Exception as e:
        logger.error(f"工具调用执行失败: {e}")
        tool_context = f"【系统内部错误】执行工具失败: {str(e)}"

    return [
        ("system",
         "你是一个专业友好的数据查询助手。请根据以下【执行结果】直接回答用户的提问，语气要自然亲切。不要在回答中直接暴露SQL或“根据数据库”之类的机械术语。"),
        ("user", f"{tool_context}\n\n我的问题是：{query}")
    ]
