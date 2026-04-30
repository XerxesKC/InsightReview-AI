from __future__ import annotations

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from app.services.data_pipeline.extractors import DataExtractionPipeline, extract_from_sources
from app.services.data_pipeline.cleaner import CleaningPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataPipelineWithCleaning:
    """
    集成抽取和清洗功能的数据管道
    """

    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config = self._load_config(config_path) if config_path else {}
        self.extraction_pipeline = None
        self.cleaning_pipeline = None
        self.extraction_result = None
        self.cleaning_results = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}

    def _build_cleaning_pipeline(self):
        """从配置构建清洗管道"""
        cleaning_pipeline = CleaningPipeline()

        sources = self.config.get('sources', [])
        for source_config in sources:
            source_name = source_config.get('name', 'unknown')
            cleaning_steps = source_config.get('cleaning_steps', [])

            if cleaning_steps:
                cleaning_pipeline.add_cleaner(source_name, cleaning_steps)
                logger.info(f"为数据源 '{source_name}' 添加了 {len(cleaning_steps)} 个清洗步骤")

        self.cleaning_pipeline = cleaning_pipeline

    def _extract_all_sources(self) -> Dict[str, pd.DataFrame]:
        """
        抽取所有数据源，按源名称分组
        """
        self.extraction_pipeline = DataExtractionPipeline(self.config_path)
        self.extraction_pipeline.load_extractors_from_config()

        all_data = []
        source_data = {}

        for extractor in self.extraction_pipeline.extractors:
            logger.info(f"正在从数据源抽取: {extractor.name}")
            try:
                df = extractor.extract()
                if not df.empty:
                    df_copy = df.copy()
                    df_copy['_source_name'] = extractor.name

                    all_data.append(df_copy)
                    source_data[extractor.name] = df_copy

                    logger.info(f"  成功抽取 {len(df)} 条记录")
                else:
                    logger.warning(f"  抽取结果为空")
                    source_data[extractor.name] = pd.DataFrame()
            except Exception as e:
                logger.error(f"  抽取失败: {e}")
                source_data[extractor.name] = pd.DataFrame()

        self.extraction_result = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

        return source_data

    def run(self) -> pd.DataFrame:
        """
        运行完整的数据管道（抽取 + 清洗）

        返回:
            清洗后的完整DataFrame
        """
        logger.info("=" * 60)
        logger.info("开始执行数据管道")
        logger.info("=" * 60)

        logger.info("\n【步骤1: 数据抽取】")
        source_data = self._extract_all_sources()

        logger.info("\n【步骤2: 构建清洗管道】")
        self._build_cleaning_pipeline()

        logger.info("\n【步骤3: 数据清洗】")

        if self.cleaning_pipeline and source_data:
            cleaned_data = {}

            for source_name, df in source_data.items():
                if not df.empty:
                    logger.info(f"\n清洗数据源: {source_name}")
                    cleaned_df = self.cleaning_pipeline.clean_source(source_name, df)
                    cleaned_data[source_name] = cleaned_df
                else:
                    cleaned_data[source_name] = df

            non_empty_dfs = [df for df in cleaned_data.values() if not df.empty]
            if non_empty_dfs:
                final_result = pd.concat(non_empty_dfs, ignore_index=True)
                if '_source_name' in final_result.columns:
                    final_result = final_result.drop(columns=['_source_name'])

                logger.info(f"\n最终合并数据: {len(final_result)} 条记录")

                self.cleaning_pipeline.print_summary()

                return final_result
        else:
            logger.warning("无清洗配置或抽取数据为空")

        logger.info("=" * 60)
        logger.info("数据管道执行完成")
        logger.info("=" * 60)

        return self.extraction_result

    def get_cleaning_summary(self) -> Dict[str, Any]:
        """获取清洗过程摘要"""
        if self.cleaning_pipeline:
            return self.cleaning_pipeline.results
        return {}


def run_pipeline_with_cleaning(config_path: str) -> pd.DataFrame:
    """
    运行完整的数据管道（抽取 + 清洗）

    参数:
        config_path: 配置文件路径

    返回:
        清洗后的DataFrame
    """
    pipeline = DataPipelineWithCleaning(config_path)
    return pipeline.run()


if __name__ == "__main__":
    config_path = "C:/Users/12550/Desktop/homework/实习/project/小众点评/review-pulse-agent/app/services/data_pipeline/sources.yaml"

    if os.path.exists(config_path):
        result_df = run_pipeline_with_cleaning(config_path)

        if not result_df.empty:
            output_path = "cleaned_extraction_results.csv"
            result_df_copy = result_df.copy()
            if 'metadata' in result_df_copy.columns:
                result_df_copy['metadata'] = result_df_copy['metadata'].apply(str)
            result_df_copy.to_csv(output_path, index=False, encoding='utf-8')
            print(f"\n结果已保存到: {output_path}")
            print(f"总记录数: {len(result_df)}")
    else:
        print(f"配置文件不存在: {config_path}")
