#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据管道入口脚本：抽取 -> 清洗 -> 模板转换 -> 导出
"""

from __future__ import annotations

import sys
import argparse
from typing import Dict, Any
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.services.data_pipeline.extractors import DataExtractionPipeline
from app.services.data_pipeline.cleaner import CleaningPipeline
from app.services.data_pipeline.template_engine import (
    TemplateEngine,
    BatchTemplateProcessor,
    load_templates_from_config
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataPipeline:
    """完整的数据处理管道"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._init_pipelines()

    def _init_pipelines(self):
        """初始化各个子管道"""
        self.extraction_pipeline = DataExtractionPipeline(self.config_path)
        self.extraction_pipeline.load_extractors_from_config()

        self.cleaning_pipeline = CleaningPipeline()
        self._setup_cleaning_steps()

        templates = load_templates_from_config(self.config_path)
        self.template_engine = TemplateEngine(templates)
        self.template_processor = BatchTemplateProcessor(self.template_engine)

        logger.info("数据管道初始化完成")

    def _setup_cleaning_steps(self):
        """从配置设置清洗步骤"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            for source in config.get('sources', []):
                name = source.get('name')
                steps = source.get('cleaning_steps', [])
                if name and steps:
                    self.cleaning_pipeline.add_cleaner(name, steps)
                    logger.info(f"为 '{name}' 添加 {len(steps)} 个清洗步骤")
        except Exception as e:
            logger.error(f"设置清洗步骤失败: {e}")

    def _extract_source_name(self, metadata_value) -> str:
        """从metadata中提取source_name"""
        try:
            if isinstance(metadata_value, dict):
                return metadata_value.get('source_name', 'unknown')
            elif isinstance(metadata_value, str):
                try:
                    return json.loads(metadata_value.replace("'", '"')).get('source_name', 'unknown')
                except:
                    return 'unknown'
            return 'unknown'
        except:
            return 'unknown'

    def run(self, export_format: str = 'csv', export_path: str = None,
            content_column: str = 'natural_language_description') -> Dict[str, pd.DataFrame]:
        """运行完整的数据管道"""
        logger.info("=" * 50)
        logger.info("开始运行数据管道")

        logger.info("步骤1: 数据抽取")
        raw_data = self.extraction_pipeline.run()

        if raw_data.empty:
            logger.warning("未抽取到数据，管道终止")
            return {}

        raw_data_by_source = {}
        for _, row in raw_data.iterrows():
            source = self._extract_source_name(row.get('metadata', 'unknown'))
            if source not in raw_data_by_source:
                raw_data_by_source[source] = []
            raw_data_by_source[source].append(row.to_dict())

        for source in raw_data_by_source:
            raw_data_by_source[source] = pd.DataFrame(raw_data_by_source[source])

        logger.info(f"共抽取 {len(raw_data_by_source)} 个数据源: {list(raw_data_by_source.keys())}")

        logger.info("步骤2: 数据清洗")
        cleaned_data = {}
        for source, df in raw_data_by_source.items():
            logger.info(f"清洗: {source}")
            cleaned_data[source] = self.cleaning_pipeline.clean_source(source, df)

        self.cleaning_pipeline.print_summary()

        logger.info("步骤3: 模板转换")
        final_data = {}
        for source, df in cleaned_data.items():
            logger.info(f"转换: {source}")
            final_data[source] = self.template_processor.process_dataframe(
                df, source, content_column
            )

        self.template_processor.print_stats()

        if export_path:
            self._export_data(final_data, export_format, export_path)

        logger.info("数据管道运行完成")
        logger.info("=" * 50)

        return final_data

    def _export_data(self, data: Dict[str, pd.DataFrame], format: str, base_path: str):
        """导出数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = Path(base_path) / f"export_{timestamp}"
        export_dir.mkdir(parents=True, exist_ok=True)

        for source, df in data.items():
            if df.empty:
                continue

            safe_name = "".join(c for c in source if c.isalnum() or c in ' -_').strip().replace(' ', '_')

            if format in ['csv', 'all']:
                path = export_dir / f"{safe_name}.csv"
                export_df = df.copy()
                if 'metadata' in export_df.columns:
                    export_df['metadata'] = export_df['metadata'].astype(str)
                export_df.to_csv(path, index=False, encoding='utf-8-sig')
                logger.info(f"导出CSV: {path}")

            if format in ['excel', 'all']:
                path = export_dir / f"{safe_name}.xlsx"
                with pd.ExcelWriter(path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=safe_name[:31], index=False)
                logger.info(f"导出Excel: {path}")

            if format in ['json', 'all']:
                path = export_dir / f"{safe_name}.json"
                df.to_json(path, orient='records', force_ascii=False, indent=2)
                logger.info(f"导出JSON: {path}")

            if 'natural_language_description' in df.columns:
                path = export_dir / f"{safe_name}_texts.txt"
                with open(path, 'w', encoding='utf-8') as f:
                    for idx, desc in enumerate(df['natural_language_description']):
                        f.write(f"{idx + 1}. {desc}\n\n")
                logger.info(f"导出文本: {path}")

        if len(data) > 1:
            combined = pd.concat([
                df.assign(source_name=source) for source, df in data.items()
            ], ignore_index=True)

            if format in ['csv', 'all']:
                combined.to_csv(export_dir / "all_data.csv", index=False, encoding='utf-8-sig')
            if format in ['json', 'all']:
                combined.to_json(export_dir / "all_data.json", orient='records', force_ascii=False, indent=2)
            logger.info(f"导出合并文件完成")


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='数据管道')

    default_config = "C:/Users/12550/Desktop/homework/实习/project/小众点评/review-pulse-agent/app/services/data_pipeline/sources.yaml"

    parser.add_argument('--config', type=str, default=default_config,
                        help='配置文件路径 (默认: %(default)s)')
    parser.add_argument('--export', type=str, default='./exports',
                        help='导出目录 (默认: %(default)s)')
    parser.add_argument('--format', type=str, choices=['csv', 'excel', 'json', 'all'],
                        default='csv', help='导出格式 (默认: %(default)s)')
    parser.add_argument('--no-export', action='store_true',
                        help='不导出数据')

    args = parser.parse_args()

    print(f"使用配置文件: {args.config}")
    print(f"导出目录: {args.export if not args.no_export else '不导出'}")
    print(f"导出格式: {args.format}")

    pipeline = DataPipeline(args.config)
    final_data = pipeline.run(
        export_format=args.format,
        export_path=None if args.no_export else args.export
    )

    print("\n" + "=" * 50)
    print("结果预览")
    for source, df in final_data.items():
        print(f"\n{source} ({len(df)} 条):")
        if 'natural_language_description' in df.columns:
            for i, desc in enumerate(df['natural_language_description'].head(3)):
                preview = desc[:100] + "..." if len(desc) > 100 else desc
                print(f"  {i + 1}. {preview}")


if __name__ == "__main__":
    main()
