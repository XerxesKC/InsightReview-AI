from __future__ import annotations

import re
import logging
from typing import Dict, Any, List, Optional, Callable
import pandas as pd
import importlib
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataCleaner:
    """
    数据清洗器，支持多种可配置的清洗步骤
    """

    def __init__(self, cleaning_steps: List[Dict[str, Any]]):
        """
        初始化清洗器

        参数:
            cleaning_steps: 清洗步骤列表，每个步骤是一个字典，包含type和其他参数
        """
        self.cleaning_steps = cleaning_steps
        self.step_results = []  

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        按顺序执行清洗步骤

        参数:
            df: 输入的DataFrame

        返回:
            清洗后的DataFrame
        """
        if df.empty:
            logger.warning("输入DataFrame为空，跳过清洗")
            return df

        result_df = df.copy()
        total_rows_before = len(result_df)

        logger.info(f"开始清洗数据，初始行数: {total_rows_before}")

        for idx, step in enumerate(self.cleaning_steps):
            step_type = step.get('type', '').lower()
            step_name = step.get('name', f'步骤{idx + 1}-{step_type}')

            rows_before = len(result_df)

            try:
                if step_type == 'regex':
                    result_df = self._apply_regex(result_df, step)
                elif step_type == 'dropna':
                    result_df = self._apply_dropna(result_df, step)
                elif step_type == 'fillna':
                    result_df = self._apply_fillna(result_df, step)
                elif step_type == 'drop_duplicates':
                    result_df = self._apply_drop_duplicates(result_df, step)
                elif step_type == 'apply':
                    result_df = self._apply_custom_function(result_df, step)
                else:
                    logger.warning(f"未知的清洗步骤类型: {step_type}，跳过")
                    continue

                rows_after = len(result_df)
                rows_removed = rows_before - rows_after

                step_result = {
                    'step': step_name,
                    'type': step_type,
                    'rows_before': rows_before,
                    'rows_after': rows_after,
                    'rows_removed': rows_removed
                }
                self.step_results.append(step_result)

                logger.info(f"  {step_name}: 行数 {rows_before} -> {rows_after} (移除 {rows_removed} 行)")

            except Exception as e:
                logger.error(f"执行清洗步骤 {step_name} 时出错: {e}")
                step_result = {
                    'step': step_name,
                    'type': step_type,
                    'error': str(e),
                    'rows_before': rows_before,
                    'rows_after': rows_before  
                }
                self.step_results.append(step_result)

        total_rows_after = len(result_df)
        total_removed = total_rows_before - total_rows_after

        logger.info(f"清洗完成，最终行数: {total_rows_after} (总计移除 {total_removed} 行)")

        return result_df

    def _apply_regex(self, df: pd.DataFrame, step: Dict[str, Any]) -> pd.DataFrame:
        """
        应用正则表达式替换

        步骤配置示例:
        - type: regex
          pattern: '\\d{4}-\\d{2}-\\d{2}'  # 匹配日期
          replace_with: '[DATE]'
          column: 'content'  # 可选，指定列，不指定则应用到所有字符串列
        """
        result_df = df.copy()

        pattern = step.get('pattern')
        replace_with = step.get('replace_with', '')
        column = step.get('column')
        flags = step.get('flags', 0)

        if not pattern:
            logger.warning("正则表达式步骤缺少pattern参数")
            return result_df

        try:
            regex = re.compile(pattern, flags)

            if column:
                if column in result_df.columns:
                    result_df[column] = result_df[column].astype(str).apply(
                        lambda x: regex.sub(replace_with, x)
                    )
                else:
                    logger.warning(f"列 '{column}' 不存在，跳过正则替换")
            else:
                for col in result_df.select_dtypes(include=['object']).columns:
                    result_df[col] = result_df[col].astype(str).apply(
                        lambda x: regex.sub(replace_with, x)
                    )
        except Exception as e:
            logger.error(f"正则替换执行失败: {e}")

        return result_df

    def _apply_dropna(self, df: pd.DataFrame, step: Dict[str, Any]) -> pd.DataFrame:
        """
        删除空值行

        步骤配置示例:
        - type: dropna
          subset: ['column1', 'column2']  # 可选，检查这些列
          how: 'any'  # 可选，'any'或'all'
        """
        subset = step.get('subset')
        how = step.get('how', 'any')

        if subset and not isinstance(subset, list):
            subset = [subset]

        return df.dropna(subset=subset, how=how)

    def _apply_fillna(self, df: pd.DataFrame, step: Dict[str, Any]) -> pd.DataFrame:
        """
        填充空值

        步骤配置示例:
        - type: fillna
          value: 'N/A'  # 填充值
          column: 'column_name'  # 可选，指定列
          或
        - type: fillna
          method: 'ffill'  # 填充方法: ffill, bfill
        """
        result_df = df.copy()

        value = step.get('value')
        method = step.get('method')
        column = step.get('column')

        if column:
            if column in result_df.columns:
                if value is not None:
                    result_df[column] = result_df[column].fillna(value)
                elif method:
                    result_df[column] = result_df[column].fillna(method=method)
            else:
                logger.warning(f"列 '{column}' 不存在，跳过填充")
        else:
            if value is not None:
                result_df = result_df.fillna(value)
            elif method:
                result_df = result_df.fillna(method=method)

        return result_df

    def _apply_drop_duplicates(self, df: pd.DataFrame, step: Dict[str, Any]) -> pd.DataFrame:
        """
        删除重复行

        步骤配置示例:
        - type: drop_duplicates
          subset: ['column1', 'column2']  # 可选，检查这些列
          keep: 'first'  # 可选，'first', 'last', False
        """
        subset = step.get('subset')
        keep = step.get('keep', 'first')

        if subset and not isinstance(subset, list):
            subset = [subset]

        return df.drop_duplicates(subset=subset, keep=keep)

    def _apply_custom_function(self, df: pd.DataFrame, step: Dict[str, Any]) -> pd.DataFrame:
        """
        应用自定义函数

        步骤配置示例:
        - type: apply
          function_path: 'scripts.custom_cleaners.my_func'
          args: []  # 可选，位置参数
          kwargs: {}  # 可选，关键字参数
        """
        function_path = step.get('function_path')

        if not function_path:
            logger.warning("自定义函数步骤缺少function_path参数")
            return df

        try:
            module_path, function_name = function_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            func = getattr(module, function_name)

            args = step.get('args', [])
            kwargs = step.get('kwargs', {})

            result = func(df, *args, **kwargs)

            if isinstance(result, pd.DataFrame):
                return result
            else:
                logger.warning(f"自定义函数应返回DataFrame，但返回了 {type(result)}")
                return df

        except ImportError as e:
            logger.error(f"导入模块失败: {e}")
            return df
        except AttributeError as e:
            logger.error(f"函数 '{function_name}' 不存在: {e}")
            return df
        except Exception as e:
            logger.error(f"执行自定义函数时出错: {e}")
            return df

    def get_cleaning_summary(self) -> Dict[str, Any]:
        """
        获取清洗过程摘要
        """
        if not self.step_results:
            return {}

        total_rows_before = self.step_results[0]['rows_before']
        total_rows_after = self.step_results[-1]['rows_after']

        return {
            'total_steps': len(self.step_results),
            'initial_rows': total_rows_before,
            'final_rows': total_rows_after,
            'rows_removed': total_rows_before - total_rows_after,
            'step_details': self.step_results
        }


class CleaningPipeline:
    """
    清洗管道，管理多个数据源的清洗流程
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.cleaners = {}
        self.results = {}

    def add_cleaner(self, source_name: str, cleaning_steps: List[Dict[str, Any]]):
        """
        为指定数据源添加清洗器
        """
        self.cleaners[source_name] = DataCleaner(cleaning_steps)

    def clean_source(self, source_name: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗指定数据源的数据
        """
        if source_name not in self.cleaners:
            logger.warning(f"数据源 '{source_name}' 没有配置清洗步骤")
            return df

        cleaner = self.cleaners[source_name]
        result_df = cleaner.clean(df)

        self.results[source_name] = cleaner.get_cleaning_summary()

        return result_df

    def clean_all(self, data_frames: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        清洗所有数据源的数据
        """
        results = {}

        for source_name, df in data_frames.items():
            if source_name in self.cleaners:
                results[source_name] = self.clean_source(source_name, df)
            else:
                results[source_name] = df
                logger.info(f"数据源 '{source_name}' 无清洗配置，保持原样")

        return results

    def print_summary(self):
        """
        打印清洗结果摘要
        """
        print("\n" + "=" * 60)
        print("数据清洗结果摘要")
        print("=" * 60)

        for source_name, summary in self.results.items():
            print(f"\n数据源: {source_name}")
            print(f"  清洗步骤数: {summary.get('total_steps', 0)}")
            print(f"  初始行数: {summary.get('initial_rows', 0)}")
            print(f"  最终行数: {summary.get('final_rows', 0)}")
            print(f"  移除行数: {summary.get('rows_removed', 0)}")

            if summary.get('step_details'):
                print("  详细步骤:")
                for step in summary['step_details']:
                    if 'error' in step:
                        print(f"    - {step['step']}: 出错 - {step['error']}")
                    else:
                        print(f"    - {step['step']}: {step['rows_before']} -> {step['rows_after']} "
                              f"(移除 {step['rows_removed']} 行)")


def remove_special_characters(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    移除指定列中的特殊字符
    """
    result_df = df.copy()
    if column in result_df.columns:
        result_df[column] = result_df[column].astype(str).apply(
            lambda x: re.sub(r'[^\w\s\u4e00-\u9fff]', '', x)
        )
    return result_df


def trim_whitespace(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
    """
    去除字符串两端的空白字符
    """
    result_df = df.copy()

    if columns is None:
        columns = result_df.select_dtypes(include=['object']).columns.tolist()

    for col in columns:
        if col in result_df.columns:
            result_df[col] = result_df[col].astype(str).str.strip()

    return result_df
