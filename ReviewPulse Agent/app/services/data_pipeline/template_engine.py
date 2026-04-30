"""
模板引擎模块 - 用于将结构化数据行转换为自然语言描述
支持从metadata中读取字段，支持解析content中的键值对
"""

from __future__ import annotations

import re
import json
import logging
from typing import Dict, Any, Optional, Set
import pandas as pd
from string import Formatter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    模板引擎，负责将DataFrame的行数据应用模板转换为自然语言
    支持从metadata字典中读取字段，支持解析content中的键值对
    """

    def __init__(self, templates_config: Dict[str, Any] = None):
        """
        初始化模板引擎

        参数:
            templates_config: 模板配置，格式如：
                {
                    '数据源名称': {
                        'template': '产品"{product_name}"售价{price}元',
                        'enabled': True,
                    }
                }
        """
        self.templates = templates_config or {}
        self._validate_templates()

    def _validate_templates(self):
        """验证模板配置的有效性"""
        for source_name, config in self.templates.items():
            template = config.get('template', '')
            if not template:
                logger.warning(f"数据源 '{source_name}' 的模板为空")
                continue

    def extract_template_fields(self, template: str) -> Set[str]:
        """
        从模板中提取字段名

        参数:
            template: 模板字符串

        返回:
            字段名集合
        """
        fields = set()
        for _, field_name, _, _ in Formatter().parse(template):
            if field_name is not None:
                fields.add(field_name)
        return fields

    def _parse_key_value_pairs(self, content: str) -> Dict[str, Any]:
        """
        解析content中的键值对格式
        支持格式如: "菜品名称: 招牌水煮鱼 | 价格: 88"

        参数:
            content: 内容字符串

        返回:
            解析出的键值对字典
        """
        result = {}
        if not isinstance(content, str):
            return result

        pattern = r'([^|,:;]+):\s*([^|,:;]+)'
        matches = re.findall(pattern, content)

        for key, value in matches:
            key = key.strip()
            value = value.strip()
            if key and value:
                result[key] = value

        return result

    def _extract_data_from_row(self, row: pd.Series) -> Dict[str, Any]:
        """
        从行数据中提取所有可用字段

        参数:
            row: DataFrame的一行数据

        返回:
            包含所有字段的字典
        """
        data_dict = {}

        for key, value in row.items():
            if key != 'metadata' and pd.notna(value):
                data_dict[key] = value

        if 'metadata' in row and pd.notna(row['metadata']):
            metadata = row['metadata']

            if isinstance(metadata, dict):
                for meta_key, meta_value in metadata.items():
                    if meta_key not in data_dict and pd.notna(meta_value):
                        data_dict[meta_key] = meta_value

            elif isinstance(metadata, str):
                try:
                    cleaned_meta = metadata.replace("'", '"')
                    metadata_dict = json.loads(cleaned_meta)
                    for meta_key, meta_value in metadata_dict.items():
                        if meta_key not in data_dict and pd.notna(meta_value):
                            data_dict[meta_key] = meta_value
                except:
                    pass

        if 'content' in data_dict and isinstance(data_dict['content'], str):
            content_str = data_dict['content']
            if ':' in content_str:
                parsed_pairs = self._parse_key_value_pairs(content_str)
                for key, value in parsed_pairs.items():
                    if key not in data_dict:
                        data_dict[key] = value

        for key in data_dict:
            if pd.isna(data_dict[key]):
                data_dict[key] = ''

        return data_dict

    def apply_template(self, row: pd.Series, template: str,
                      source_name: str = None) -> str:
        """
        将模板应用到单行数据

        参数:
            row: DataFrame的一行数据
            template: 模板字符串
            source_name: 数据源名称

        返回:
            生成的文本
        """
        try:
            data_dict = self._extract_data_from_row(row)

            result = template.format(**data_dict)
            return result

        except KeyError as e:
            missing_field = str(e).strip("'")
            logger.warning(f"模板字段缺失: {missing_field}")

            return self._generate_default_text(row)

        except Exception as e:
            logger.error(f"模板应用失败: {e}")
            return self._generate_default_text(row)

    def _generate_default_text(self, row: pd.Series) -> str:
        """生成默认文本"""
        parts = []

        if 'content' in row and pd.notna(row['content']):
            content = row['content']
            if isinstance(content, str) and ':' in content:
                parsed = self._parse_key_value_pairs(content)
                if parsed:
                    for key, value in parsed.items():
                        parts.append(f"{key}: {value}")
                    return " | ".join(parts)

        for key, value in row.items():
            if key != 'metadata' and pd.notna(value):
                parts.append(f"{key}: {value}")

        return " | ".join(parts) if parts else "空数据记录"

    def get_template_for_source(self, source_name: str) -> Optional[str]:
        """获取指定数据源的模板"""
        config = self.templates.get(source_name)
        if config and config.get('enabled', True):
            return config.get('template')
        return None

    def add_template(self, source_name: str, template: str,
                    enabled: bool = True):
        """添加或更新模板"""
        self.templates[source_name] = {
            'template': template,
            'enabled': enabled,
        }
        logger.info(f"已添加模板 for '{source_name}'")


class BatchTemplateProcessor:
    """
    批量模板处理器
    """

    def __init__(self, template_engine: TemplateEngine):
        self.template_engine = template_engine
        self.processing_stats = {}

    def process_dataframe(self, df: pd.DataFrame, source_name: str,
                         content_column: str = 'natural_language_description') -> pd.DataFrame:
        """
        处理DataFrame，添加自然语言描述列
        """
        if df.empty:
            logger.warning(f"DataFrame为空: {source_name}")
            df[content_column] = []
            return df

        result_df = df.copy()
        template = self.template_engine.get_template_for_source(source_name)

        start_time = pd.Timestamp.now()
        success_count = 0

        if template:
            logger.info(f"应用模板 for '{source_name}': {template}")

            descriptions = []
            for idx, row in df.iterrows():
                try:
                    desc = self.template_engine.apply_template(row, template, source_name)
                    descriptions.append(desc)
                    success_count += 1
                except Exception as e:
                    logger.error(f"处理第{idx}行失败: {e}")
                    descriptions.append(self.template_engine._generate_default_text(row))

            result_df[content_column] = descriptions

        else:
            logger.info(f"数据源 '{source_name}' 无模板配置，使用默认格式")
            descriptions = []
            for _, row in df.iterrows():
                desc = self.template_engine._generate_default_text(row)
                descriptions.append(desc)
            result_df[content_column] = descriptions
            success_count = len(df)

        self.processing_stats[source_name] = {
            'total_rows': len(df),
            'success_count': success_count,
            'processing_time': (pd.Timestamp.now() - start_time).total_seconds(),
            'template_used': template is not None
        }

        return result_df

    def process_multiple(self, data_frames: Dict[str, pd.DataFrame],
                        content_column: str = 'natural_language_description') -> Dict[str, pd.DataFrame]:
        """处理多个DataFrame"""
        results = {}
        for source_name, df in data_frames.items():
            results[source_name] = self.process_dataframe(df, source_name, content_column)
        return results

    def print_stats(self):
        """打印处理统计信息"""
        print("\n" + "=" * 60)
        print("模板处理统计")
        print("=" * 60)

        for source_name, stats in self.processing_stats.items():
            print(f"\n数据源: {source_name}")
            print(f"  总行数: {stats['total_rows']}")
            print(f"  成功: {stats['success_count']}")
            print(f"  处理时间: {stats['processing_time']:.2f}秒")
            print(f"  使用模板: {'是' if stats['template_used'] else '否'}")


def load_templates_from_config(config_path: str) -> Dict[str, Any]:
    """
    从YAML配置文件加载模板配置
    """
    import yaml

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        templates = {}
        sources = config.get('sources', [])

        for source in sources:
            name = source.get('name')
            template_config = source.get('template_config', {})

            if name and template_config.get('template'):
                templates[name] = {
                    'template': template_config['template'],
                    'enabled': template_config.get('enabled', True),
                }
                logger.info(f"从配置加载模板 for '{name}': {template_config['template']}")

        return templates

    except Exception as e:
        logger.error(f"加载模板配置失败: {e}")
        return {}


if __name__ == "__main__":
    import pandas as pd

    test_df = pd.DataFrame({
        'content': [
            '菜品名称: 招牌水煮鱼 | 价格: 88 | 类别: 招牌菜'
        ],
        'metadata': [{'source_name': '菜单数据'}]
    })

    templates = {
        '菜单数据': {
            'template': '【{菜品名称}】价格：{价格}元，类别：{类别}',
            'enabled': True
        }
    }

    engine = TemplateEngine(templates)
    processor = BatchTemplateProcessor(engine)
    result = processor.process_dataframe(test_df, '菜单数据')
    print(result['natural_language_description'].iloc[0])
