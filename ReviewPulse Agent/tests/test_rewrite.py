import asyncio
import os
import sys
import time  
from dotenv import load_dotenv

load_dotenv()

from app.rag.llm import rewrite_question


async def run_test_cases():
    print("=" * 50)
    print("🚀 开始测试 LLM 问题改写引擎")
    print("=" * 50)

    mock_history = [
        {
            "turn_no": 1,
            "query": "川香居的菜品有哪些？",
            "answer": "根据知识库检索，川香居暂未收录完整的菜单列表。不过，文档中包含了部分菜品的具体名称及相关口味调整说明。"
        }
    ]

    test_cases = [
        "开车去那里方便么",  
        "重复回答一下我刚刚的问题",  
        "他们家有包厢吗？",  
        "系统怎么用",  
    ]

    for i, current_question in enumerate(test_cases, 1):
        print(f"\n▶️ [测试用例 {i}]")
        print(f"  历史记录: 第1轮用户问了「{mock_history[0]['query']}」")
        print(f"  当前问题: 「{current_question}」")
        print("  ⏳ 正在调用大模型进行改写...")

        try:
            start_time = time.monotonic()

            rewritten_query = await rewrite_question(
                question=current_question,
                history_turns=mock_history
            )

            end_time = time.monotonic()
            elapsed_time = end_time - start_time

            print(f"  ✅ 改写结果: 👉 「{rewritten_query}」 (耗时: {elapsed_time:.2f} 秒)")
        except Exception as e:
            print(f"  ❌ 调用失败: {e}")


if __name__ == "__main__":
    asyncio.run(run_test_cases())
