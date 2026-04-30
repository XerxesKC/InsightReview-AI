#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据管道入口脚本：抽取 -> 清洗 -> 模板转换 -> 文本切分 -> 导出
支持语义和递归两种文本切分策略
"""

from __future__ import annotations

import sys
from typing import Dict, Any, Optional
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import json
import yaml

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.services.data_pipeline.extractors import DataExtractionPipeline
from app.services.data_pipeline.cleaner import CleaningPipeline
from app.services.data_pipeline.template_engine import (
    TemplateEngine,
    BatchTemplateProcessor,
    load_templates_from_config
)
from app.services.data_pipeline.text_splitter import split_dataframe_text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self._init_pipelines()
        self.split_stats = {}

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def _init_pipelines(self):
        self.extraction_pipeline = DataExtractionPipeline(self.config_path)
        self.extraction_pipeline.load_extractors_from_config()

        self.cleaning_pipeline = CleaningPipeline()
        self._setup_cleaning_steps()

        templates = load_templates_from_config(self.config_path)
        self.template_engine = TemplateEngine(templates)
        self.template_processor = BatchTemplateProcessor(self.template_engine)

    def _setup_cleaning_steps(self):
        try:
            for source in self.config.get('sources', []):
                name = source.get('name')
                steps = source.get('cleaning_steps', [])
                if name and steps:
                    self.cleaning_pipeline.add_cleaner(name, steps)
        except Exception as e:
            logger.error(f"设置清洗步骤失败: {e}")

    def _extract_source_name(self, metadata) -> str:
        try:
            if isinstance(metadata, dict):
                return metadata.get('source_name', 'unknown')
            elif isinstance(metadata, str):
                return json.loads(metadata.replace("'", '"')).get('source_name', 'unknown')
            return 'unknown'
        except:
            return 'unknown'

    def _get_source_type(self, metadata) -> str:
        try:
            if isinstance(metadata, dict):
                return metadata.get('source_type', 'unknown')
            elif isinstance(metadata, str):
                return json.loads(metadata.replace("'", '"')).get('source_type', 'unknown')
            return 'unknown'
        except:
            return 'unknown'

    def _is_tabular(self, source_type: str) -> bool:
        return source_type in ['csv_excel', 'excel', 'csv']

    def _group_by_source(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        if df.empty:
            return {}

        result = {}
        for _, row in df.iterrows():
            source = self._extract_source_name(row.get('metadata', 'unknown'))
            if source not in result:
                result[source] = []
            result[source].append(row.to_dict())

        return {k: pd.DataFrame(v) for k, v in result.items()}

    def run(self, export_path: str = None,
            splitter_type: Optional[str] = None,
            chunk_size: int = 500,
            chunk_overlap: int = 50,
            similarity_threshold: float = 0.7,
            model_name: str = "data/bge-model/BAAI/bge-base-zh-v1.5") -> Dict[str, pd.DataFrame]:

        logger.info("=" * 60)
        logger.info("开始运行数据管道")

        raw_data = self.extraction_pipeline.run()
        if raw_data.empty:
            logger.warning("未抽取到数据")
            return {}

        raw_by_source = self._group_by_source(raw_data)
        logger.info(f"共抽取 {len(raw_by_source)} 个数据源")

        cleaned = {}
        for source, df in raw_by_source.items():
            logger.info(f"清洗: {source}")
            cleaned[source] = self.cleaning_pipeline.clean_source(source, df)

        converted = {}
        for source, df in cleaned.items():
            logger.info(f"转换: {source}")

            source_type = self._get_source_type(df.iloc[0].get('metadata', {})) if not df.empty else 'unknown'
            is_tabular = self._is_tabular(source_type)

            if is_tabular:
                converted[source] = self.template_processor.process_dataframe(
                    df, source, 'natural_language_description'
                )
                text_col = 'natural_language_description'
            else:
                converted_df = df.copy()
                if 'content' not in converted_df.columns:
                    converted_df['content'] = converted_df.get('content', '')
                converted[source] = converted_df
                text_col = 'content'

            logger.info(f"  使用文本列: {text_col}")

        final_data = converted
        if splitter_type:
            logger.info(f"开始切分 - 策略: {splitter_type}")
            for source, df in converted.items():
                source_type = self._get_source_type(df.iloc[0].get('metadata', {})) if not df.empty else 'unknown'
                text_col = 'natural_language_description' if self._is_tabular(source_type) else 'content'

                result = split_dataframe_text(
                    df=df,
                    text_column=text_col,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    splitter_type=splitter_type,
                    similarity_threshold=similarity_threshold,
                    model_name=model_name
                )
                final_data[source] = result

                chunk_lens = result['chunk_text'].str.len()
                self.split_stats[source] = {
                    '原行数': len(df),
                    '块数': len(result),
                    '平均大小': f"{chunk_lens.mean():.0f}",
                    '范围': f"{chunk_lens.min()}-{chunk_lens.max()}"
                }

        if export_path:
            self._export(final_data, export_path, splitter_type)

        return final_data

    def _export(self, data: Dict[str, pd.DataFrame], base_path: str, splitter_type: Optional[str] = None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"export_{splitter_type}_{timestamp}" if splitter_type else f"export_{timestamp}"
        export_dir = Path(base_path) / name
        export_dir.mkdir(parents=True, exist_ok=True)

        for source, df in data.items():
            if df.empty:
                continue

            safe_name = "".join(c for c in source if c.isalnum() or c in ' -_').strip().replace(' ', '_')
            path = export_dir / f"{safe_name}.csv"

            export_df = df.copy()
            if 'metadata' in export_df.columns:
                export_df['metadata'] = export_df['metadata'].astype(str)

            export_df.to_csv(path, index=False, encoding='utf-8-sig')
            logger.info(f"导出: {path.name}")

        if self.split_stats:
            with open(export_dir / "stats.json", 'w', encoding='utf-8') as f:
                json.dump(self.split_stats, f, ensure_ascii=False, indent=2)


def main():
    CONFIG_PATH = "C:/Users/12550/Desktop/homework/实习/project/小众点评/review-pulse-agent/app/services/data_pipeline/sources.yaml"
    EXPORT_PATH = "./exports"
    SPLITTER_TYPE = "semantic"  
    CHUNK_SIZE = 200
    CHUNK_OVERLAP = 50
    SIMILARITY_THRESHOLD = 0.7
    MODEL_NAME = "data/bge-model/BAAI/bge-base-zh-v1.5"

    print("\n" + "=" * 60)
    print("数据管道配置")
    print("=" * 60)
    print(f"切分策略: {SPLITTER_TYPE}")
    print(f"块大小: {CHUNK_SIZE}")
    print(f"重叠: {CHUNK_OVERLAP}")
    print("=" * 60)

    pipeline = DataPipeline(CONFIG_PATH)
    final_data = pipeline.run(
        export_path=EXPORT_PATH,
        splitter_type=SPLITTER_TYPE,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        similarity_threshold=SIMILARITY_THRESHOLD,
        model_name=MODEL_NAME
    )

    print("\n" + "=" * 60)
    print("结果预览")
    for source, df in final_data.items():
        print(f"\n{source} ({len(df)} 条):")
        if source in pipeline.split_stats:
            s = pipeline.split_stats[source]
            print(f"  统计: {s['块数']}块, 平均{s['平均大小']}字符, 范围{s['范围']}")

        preview_col = 'chunk_text' if 'chunk_text' in df.columns else 'content'
        if preview_col in df.columns:
            for i in range(min(2, len(df))):
                text = str(df.iloc[i][preview_col])[:100]
                print(f"  {i + 1}. {text}...")


if __name__ == "__main__":
    main()
