from __future__ import annotations

import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from pypdf import PdfReader
from docx import Document

class DataSourceExtractor:
    """
    数据源抽取器基类
    """

    def __init__(self, source_config: Dict[str, Any]):
        self.config = source_config
        self.name = source_config.get('name', 'unknown')
        self.type = source_config.get('type', 'unknown')
        self.enabled = source_config.get('enabled', True)

    def extract(self) -> pd.DataFrame:
        """抽取数据并返回标准格式的DataFrame"""
        raise NotImplementedError("子类必须实现extract方法")

    def _create_metadata(self, **kwargs) -> Dict[str, Any]:
        """创建标准的元数据字典"""
        metadata = {
            'source_name': self.name,
            'source_type': self.type,
            'extract_time': pd.Timestamp.now().isoformat(),
        }
        metadata.update(kwargs)
        return metadata

    def _get_absolute_path(self, path: str) -> str:
        """将路径转换为绝对路径"""
        if not path:
            return path

        path = path.replace('\\', '/')

        if os.path.isabs(path):
            return path

        return str(Path.cwd() / path)


class FileSystemExtractor(DataSourceExtractor):
    """
    文件系统抽取器 - 支持PDF、DOCX、MD文件
    """

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.base_path = source_config.get('base_path', '')
        self.file_patterns = source_config.get('file_patterns', ['**/*.pdf', '**/*.docx', '**/*.md', '**/*.txt'])
        self.recursive = source_config.get('recursive', True)
        self.encoding = source_config.get('encoding', 'utf-8')

    def extract(self) -> pd.DataFrame:
        """从文件系统抽取数据"""
        if not self.enabled:
            return pd.DataFrame(columns=['content', 'metadata'])

        base_path = self._get_absolute_path(self.base_path)
        if not os.path.exists(base_path):
            print(f"路径不存在: {base_path}")
            return pd.DataFrame(columns=['content', 'metadata'])

        all_contents = []
        base_path_obj = Path(base_path)

        for pattern in self.file_patterns:
            files = base_path_obj.glob(pattern) if self.recursive else base_path_obj.glob(pattern.replace('**/', ''))

            for file_path in files:
                if file_path.is_file():
                    try:
                        content = self._parse_file(file_path)
                        if content and content.strip():
                            metadata = self._create_metadata(
                                file_path=str(file_path),
                                file_name=file_path.name,
                                file_size=file_path.stat().st_size,
                                file_type=file_path.suffix.lower()
                            )
                            all_contents.append({
                                'content': content,
                                'metadata': metadata
                            })
                    except Exception as e:
                        print(f"解析文件失败 {file_path}: {e}")

        return pd.DataFrame(all_contents)

    def _parse_file(self, file_path: Path) -> str:
        """根据文件类型解析文件"""
        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return self._extract_pdf(file_path)
        elif suffix == '.docx':
            return self._extract_docx(file_path)
        elif suffix == '.md':
            return self._extract_markdown(file_path)
        elif suffix == '.txt':
            return self._extract_txt(file_path)
        else:
            return ""

    def _extract_txt(self, file_path: Path) -> str:
        """解析TXT文件，支持多种编码"""
        encodings = [self.encoding, 'utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception:
                continue

        try:
            with open(file_path, 'rb') as f:
                return f.read().decode('utf-8', errors='ignore')
        except:
            return ""

    def _extract_pdf(self, file_path: Path) -> str:
        """解析PDF文件"""
        try:
            text_content = []
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            return '\n\n'.join(text_content)
        except Exception as e:
            print(f"PDF解析错误: {e}")
            return ""

    def _extract_docx(self, file_path: Path) -> str:
        """解析DOCX文件"""
        try:
            doc = Document(file_path)
            paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
            return '\n'.join(paragraphs)
        except Exception as e:
            print(f"DOCX解析错误: {e}")
            return ""

    def _extract_markdown(self, file_path: Path) -> str:
        """解析Markdown文件"""
        try:
            with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"MD解析错误: {e}")
            return ""


class CSVExcelExtractor(DataSourceExtractor):
    """
    CSV/Excel文件抽取器
    """

    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
        self.file_path = source_config.get('file_path', '')
        self.sheet_name = source_config.get('sheet_name', 0)
        self.encoding = source_config.get('encoding', 'utf-8')
        self.sep = source_config.get('separator', ',')
        self.header = source_config.get('header', 0)

    def extract(self) -> pd.DataFrame:
        """从CSV或Excel文件抽取数据"""
        if not self.enabled:
            return pd.DataFrame(columns=['content', 'metadata'])

        file_path = self._get_absolute_path(self.file_path)
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return pd.DataFrame(columns=['content', 'metadata'])

        path = Path(file_path)
        suffix = path.suffix.lower()

        try:
            if suffix in ['.csv', '.txt']:
                df = self._read_csv(file_path)
            elif suffix in ['.xls', '.xlsx']:
                df = self._read_excel(file_path)
            else:
                return pd.DataFrame(columns=['content', 'metadata'])

            return self._convert_to_standard_format(df, path)
        except Exception as e:
            print(f"解析文件失败: {e}")
            return pd.DataFrame(columns=['content', 'metadata'])

    def _read_csv(self, file_path: str) -> pd.DataFrame:
        """读取CSV文件"""
        encodings = [self.encoding, 'utf-8', 'gbk', 'latin-1']
        separators = [self.sep, ',', ';', '\t']

        for encoding in encodings:
            for sep in separators:
                try:
                    return pd.read_csv(
                        file_path,
                        encoding=encoding,
                        sep=sep,
                        header=self.header if self.header is not None else 'infer',
                        on_bad_lines='skip',
                        nrows=1000  
                    )
                except:
                    continue
        return pd.DataFrame()

    def _read_excel(self, file_path: str) -> pd.DataFrame:
        """读取Excel文件"""
        try:
            return pd.read_excel(
                file_path,
                sheet_name=self.sheet_name,
                header=self.header,
                nrows=1000  
            )
        except:
            return pd.DataFrame()

    def _convert_to_standard_format(self, df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
        """将DataFrame的每一行转换为标准格式"""
        if df.empty:
            return pd.DataFrame(columns=['content', 'metadata'])

        records = []
        for idx, row in df.iterrows():
            row_parts = []
            for col in df.columns:
                val = row[col]
                if pd.notna(val):
                    row_parts.append(f"{col}: {val}")

            content = " | ".join(row_parts)

            metadata = self._create_metadata(
                file_path=str(file_path),
                file_name=file_path.name,
                file_type=file_path.suffix.lower(),
                row_index=idx,
                total_rows=len(df)
            )

            records.append({
                'content': content,
                'metadata': metadata
            })

        return pd.DataFrame(records)


class ExtractorFactory:
    """抽取器工厂类"""

    @staticmethod
    def create_extractor(source_config: Dict[str, Any]) -> Optional[DataSourceExtractor]:
        source_type = source_config.get('type', '').lower()

        if source_type == 'filesystem':
            return FileSystemExtractor(source_config)
        elif source_type == 'csv_excel':
            return CSVExcelExtractor(source_config)
        else:
            print(f"不支持的数据源类型: {source_type}")
            return None


class DataExtractionPipeline:
    """数据抽取管道"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path) if config_path else {}
        self.extractors = []

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}

    def load_extractors_from_config(self):
        """从配置加载抽取器"""
        sources = self.config.get('sources', [])
        for source_config in sources:
            extractor = ExtractorFactory.create_extractor(source_config)
            if extractor:
                self.extractors.append(extractor)

    def run(self) -> pd.DataFrame:
        """运行抽取管道"""
        all_data = []

        for extractor in self.extractors:
            print(f"正在从数据源抽取: {extractor.name}")
            try:
                df = extractor.extract()
                if not df.empty:
                    all_data.append(df)
                    print(f"  成功抽取 {len(df)} 条记录")
            except Exception as e:
                print(f"  抽取失败: {e}")

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame(columns=['content', 'metadata'])


def extract_from_sources(config_path: str) -> pd.DataFrame:
    """从配置文件抽取数据"""
    pipeline = DataExtractionPipeline(config_path)
    pipeline.load_extractors_from_config()
    return pipeline.run()


def extract_from_filesystem(base_path: str) -> pd.DataFrame:
    """快速从文件系统抽取数据"""
    config = {
        'sources': [{
            'name': '文件系统',
            'type': 'filesystem',
            'enabled': True,
            'base_path': base_path,
            'file_patterns': ['**/*.pdf', '**/*.docx', '**/*.md'],
            'recursive': True
        }]
    }
    pipeline = DataExtractionPipeline()
    pipeline.load_extractors_from_config(config)
    return pipeline.run()


def extract_from_csv_excel(file_path: str) -> pd.DataFrame:
    """快速从CSV/Excel文件抽取数据"""
    config = {
        'sources': [{
            'name': '表格文件',
            'type': 'csv_excel',
            'enabled': True,
            'file_path': file_path
        }]
    }
    pipeline = DataExtractionPipeline()
    pipeline.load_extractors_from_config(config)
    return pipeline.run()


if __name__ == "__main__":
    df = extract_from_sources('sources.yaml')
    print(df)

    df_copy = df.copy()
    df_copy['metadata'] = df_copy['metadata'].apply(str)
    df_copy.to_csv('extraction_results.csv', index=False, encoding='utf-8')

    print("\n结果已保存到 extraction_results.json 和 extraction_results.csv")
