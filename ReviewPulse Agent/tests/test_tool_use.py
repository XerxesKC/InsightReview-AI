import asyncio
import os
import sys
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

load_dotenv(os.path.join(project_root, ".env"))

from app.tools.executor import process_tool_use_intent
from app.rag.llm import invoke_chat_stream


class MockRow:
    """模拟 SQLAlchemy 返回的数据行"""

    def __init__(self, title, content, like_count, create_time):
        self.title = title
        self.content = content
        self.like_count = like_count
        self.create_time = create_time


class MockResult:
    """模拟 SQLAlchemy 的执行结果"""

    def fetchone(self):
        return MockRow(
            title="七夕限定套装",
            content="「星河之恋」礼盒接受预定...",
            like_count=688,
            create_time="2023-07-25 14:00:00"
        )


class MockSession:
    """模拟异步的 SQLAlchemy Session"""

    async def execute(self, sql, params=None):
        print(f"\n    [Mock DB] 🗄️ 正在执行 SQL 查询...")
        print(f"    [Mock DB] 传入参数: {params}")
        await asyncio.sleep(0.5)
        return MockResult()


async def run_test_cases():
    print("=" * 60)
    print("🚀 开始测试 LLM 工具调用 (Tool Use) 与流式输出引擎")
    print("=" * 60)

    mock_user = {
        "user_id": "1",
        "user_type": "merchant"
    }

    mock_session = MockSession()
    model_name = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")

    test_cases = [
        "帮我查一下我店铺里点赞数最多的动态是哪个？",
        "1号商家最火的帖子是什么？",
    ]

    for i, query in enumerate(test_cases, 1):
        print(f"\n▶️ [测试用例 {i}]")
        print(f"  🧑 用户提问: 「{query}」")
        print("  ⏳ [Step 1] 正在调用大模型进行意图识别和参数提取...")

        try:
            tool_chat_messages = await process_tool_use_intent(
                query=query,
                user=mock_user,
                session=mock_session,
                model_name=model_name
            )

            print(f"\n  ✅ [Step 2] 工具调用完成，准备给大模型生成的 Prompt Context 如下:")
            for msg in tool_chat_messages:
                content_preview = msg[1].replace("\n", " ")[:80] + "..."
                print(f"      - {msg[0].upper()}: {content_preview}")

            print("\n  ⏳ [Step 3] 正在调用大模型进行流式输出 (Stream)...")
            print("  🤖 助手回答: ", end="", flush=True)

            stream_generator = invoke_chat_stream(
                messages=tool_chat_messages,
                model_name=model_name,
            )

            async for chunk in stream_generator:
                print(chunk, end="", flush=True)
            print("\n" + "-" * 40)

        except Exception as e:
            print(f"\n  ❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(run_test_cases())
