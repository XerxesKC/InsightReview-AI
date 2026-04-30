#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成模型微调数据集脚本

该脚本从数据库中收集对话和评分数据，转换为JSONL格式的数据集，用于模型微调。
支持按评分过滤数据，如只导出被"赞"的对话。
"""

import os
import json
import argparse
import random
from datetime import datetime

import asyncio
from sqlalchemy import create_engine, select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.models import ChatSession, ChatTurn
from app.core.config import get_settings


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="生成模型微调数据集")
    parser.add_argument(
        "--output",
        type=str,
        default="../data/finetune/bge_training_data.jsonl",
        help="输出JSONL文件路径"
    )
    parser.add_argument(
        "--rating",
        type=int,
        choices=[-1, 0, 1],
        help="按评分过滤，-1=踩, 0=未评分, 1=赞"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="限制输出数据条数"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="bge",
        choices=["openai", "generic", "bge"],
        help="输出格式，openai=OpenAI格式, generic=通用格式, bge=BGE模型格式"
    )
    return parser.parse_args()


async def fetch_chat_data(session, rating=None, limit=None):
    """从数据库获取聊天数据"""
    stmt = select(ChatTurn)
    
    if rating is not None:
        stmt = stmt.where(ChatTurn.rating == rating)
    else:
        stmt = stmt.where(ChatTurn.rating.in_([1, -1]))
    
    stmt = stmt.order_by(ChatTurn.created_at.desc())
    
    if limit:
        stmt = stmt.limit(limit)
    
    result = await session.execute(stmt)
    chat_turns = result.scalars().all()
    
    return chat_turns


def format_openai(chat_turns):
    """格式化为OpenAI微调格式"""
    data = []
    for turn in chat_turns:
        messages = [
            {"role": "user", "content": turn.query},
            {"role": "assistant", "content": turn.answer}
        ]
        
        metadata = {
            "session_id": turn.session_id,
            "turn_no": turn.turn_no,
            "rating": turn.rating,
            "created_at": turn.created_at.isoformat() if turn.created_at else None
        }
        
        sample = {
            "messages": messages,
            "metadata": metadata
        }
        data.append(sample)
    return data


def format_generic(chat_turns):
    """格式化为通用微调格式"""
    data = []
    for turn in chat_turns:
        sample = {
            "input": turn.query,
            "output": turn.answer,
            "session_id": turn.session_id,
            "turn_no": turn.turn_no,
            "rating": turn.rating,
            "created_at": turn.created_at.isoformat() if turn.created_at else None
        }
        data.append(sample)
    return data


def parse_sources(sources_str):
    """解析sources字段"""
    if not sources_str:
        return []
    try:
        return json.loads(sources_str)
    except json.JSONDecodeError:
        return []


def format_bge(chat_turns):
    """格式化为BGE模型训练格式（聚合三元组格式）"""
    all_docs_pool = []
    for turn in chat_turns:
        sources = parse_sources(turn.sources)
        for s in sources:
            content = s.get("content", "").strip()
            if content:
                all_docs_pool.append(content)
    
    if not all_docs_pool:
        return []

    grouped_data = {}
    for turn in chat_turns:
        query = turn.query.strip()
        if not query:
            continue
            
        if query not in grouped_data:
            grouped_data[query] = {"query": query, "pos": [], "neg": []}
        
        sources = parse_sources(turn.sources)
        for source in sources:
            content = source.get("content", "").strip()
            if not content:
                continue
            
            if turn.rating == 1:
                if content not in grouped_data[query]["pos"]:
                    grouped_data[query]["pos"].append(content)
            elif turn.rating == -1:
                if content not in grouped_data[query]["neg"]:
                    grouped_data[query]["neg"].append(content)

    final_data = []
    for q_item in grouped_data.values():
        if not q_item["pos"]:
            continue
            
        if not q_item["neg"]:
            random_neg = random.choice(all_docs_pool)
            if random_neg not in q_item["pos"]:
                q_item["neg"].append(random_neg)
            else:
                continue
        
        final_data.append(q_item)
        
    return final_data


async def main():
    """主函数"""
    args = parse_args()
    settings = get_settings()
    
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        chat_turns = await fetch_chat_data(session, args.rating, args.limit)
        
        if args.format == "openai":
            data = format_openai(chat_turns)
        elif args.format == "bge":
            data = format_bge(chat_turns)
        else:
            data = format_generic(chat_turns)

        with open(args.output, "w", encoding="utf-8") as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write("\n")
        
        print(f"成功生成 {len(data)} 条数据，保存到 {args.output}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
