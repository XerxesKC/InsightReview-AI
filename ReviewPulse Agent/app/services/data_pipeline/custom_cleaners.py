"""
自定义清洗函数示例
可以在sources.yaml中通过function_path引用
"""

import re
import pandas as pd


def clean_phone_numbers(df: pd.DataFrame, column: str = 'content') -> pd.DataFrame:
    """
    清洗电话号码，统一格式
    """
    result_df = df.copy()

    if column in result_df.columns:
        def format_phone(text):
            if pd.isna(text):
                return text
            numbers = re.sub(r'\D', '', str(text))
            if len(numbers) == 11:
                return f"{numbers[:3]}-{numbers[3:7]}-{numbers[7:]}"
            elif len(numbers) == 8:
                return f"{numbers[:4]}-{numbers[4:]}"
            return str(text)

        result_df[column] = result_df[column].apply(format_phone)

    return result_df


def extract_emails(df: pd.DataFrame, column: str = 'content', new_column: str = 'email') -> pd.DataFrame:
    """
    从文本中提取邮箱地址
    """
    result_df = df.copy()

    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    if column in result_df.columns:
        emails = result_df[column].astype(str).apply(
            lambda x: re.findall(email_pattern, x)[0] if re.findall(email_pattern, x) else None
        )
        result_df[new_column] = emails

    return result_df


def normalize_rating(df: pd.DataFrame, column: str = 'content') -> pd.DataFrame:
    """
    规范化评分（将各种评分格式转为1-5分制）
    """
    result_df = df.copy()

    if column in result_df.columns:
        def convert_rating(text):
            if pd.isna(text):
                return text

            text = str(text).strip()

            patterns = [
                (r'(\d+(?:\.\d+)?)\s*[／/]\s*5', 1.0),  
                (r'(\d+(?:\.\d+)?)\s*[／/]\s*10', 0.5),  
                (r'(\d+(?:\.\d+)?)\s*分', 1.0),  
                (r'(\d+(?:\.\d+)?)\s*星', 1.0),  
                (r'(\d+(?:\.\d+)?)\s*[级級]', 1.0),  
            ]

            for pattern, multiplier in patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        rating = float(match.group(1)) * multiplier
                        return min(5.0, max(0.0, rating))  
                    except:
                        pass

            return text

        result_df[column] = result_df[column].apply(convert_rating)

    return result_df


def add_source_tag(df: pd.DataFrame, tag: str) -> pd.DataFrame:
    """
    为每条数据添加来源标签
    """
    result_df = df.copy()
    result_df['source_tag'] = tag
    return result_df


def filter_by_length(df: pd.DataFrame, column: str = 'content', min_length: int = 10) -> pd.DataFrame:
    """
    过滤掉内容太短的记录
    """
    if column in df.columns:
        mask = df[column].astype(str).str.len() >= min_length
        return df[mask]
    return df
