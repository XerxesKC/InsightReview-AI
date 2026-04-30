#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微调BGE模型脚本
修正版：支持三元组排序损失函数
"""

import json
import argparse
import torch

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="微调BGE模型")
    parser.add_argument(
        "--data",
        type=str,
        default="../data/finetune/bge_training_data.jsonl",
        help="训练数据文件路径"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="../data/bge-model/BAAI/bge-large-zh-v1.5",
        help="预训练模型名称或路径"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../data/bge-model/BAAI/bge-large-zh-v1.5-finetuned",
        help="微调后模型保存路径"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=4,  
        help="训练批次大小"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="训练轮数"
    )
    parser.add_argument(
        "--warmup_steps",
        type=int,
        default=10,
        help="预热步数"
    )
    return parser.parse_args()


def load_data(data_path):
    """加载训练数据：适配 [Query, Pos, Neg] 三元组"""
    examples = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                query = item["query"]
                pos = item["pos"][0] if isinstance(item.get("pos"), list) and item["pos"] else ""
                neg = item["neg"][0] if isinstance(item.get("neg"), list) and item["neg"] else ""

                if query and pos:
                    texts = [query, pos]
                    if neg:
                        texts.append(neg)

                    example = InputExample(texts=texts)
                    examples.append(example)
            except Exception as e:
                print(f"跳过错误行: {e}")
                continue
    return examples


def main():
    """主函数"""
    args = parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"当前运行设备: {device}")

    print(f"加载训练数据: {args.data}")
    train_examples = load_data(args.data)
    print(f"加载了 {len(train_examples)} 条训练数据")

    if not train_examples:
        print("错误：没有可用的训练数据，请检查数据生成脚本。")
        return

    print(f"加载预训练模型: {args.model}")
    model = SentenceTransformer(args.model, device=device)

    train_dataloader = DataLoader(
        train_examples,
        shuffle=True,
        batch_size=args.batch_size
    )

    train_loss = losses.MultipleNegativesRankingLoss(model)

    print("开始训练模型...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=args.epochs,
        warmup_steps=args.warmup_steps,
        output_path=args.output,
        show_progress_bar=True
    )

    print(f"训练完成，模型保存到: {args.output}")


if __name__ == "__main__":
    main()
