"""
Pandas分析服务 - 支持自然语言数据分析
"""

import asyncio
import base64
import json
import logging
import re
import traceback
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import unquote

import pandas as pd
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.db.models import Document
from e2b_code_interpreter import Sandbox
import os
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)
settings = get_settings()
E2B_API_KEY = os.environ.get("E2B_API_KEY") or ""
API_KEY = os.environ.get("API_KEY") or settings.api_key


def _resolve_local_file_path(file_path: str | None) -> Optional[str]:
    if not file_path:
        return None

    raw_path = Path(str(file_path).strip())
    if raw_path.is_absolute():
        return str(raw_path) if raw_path.exists() else None

    module_path = Path(__file__).resolve()
    candidates = [
        Path.cwd() / raw_path,
        module_path.parents[2] / raw_path,
        module_path.parents[3] / raw_path,
        Path(settings.upload_dir) / raw_path.name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


class PandasSandboxExecutor:
    """沙箱执行器：使用 e2b_code_interpreter.Sandbox。"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.enable_chart = False
        self._init_error: Optional[str] = None

    async def execute(
        self,
        code: str,
        df: pd.DataFrame,
        dataset_reference: Optional[str] = None,
        max_rows: int = 10000,
    ) -> Dict[str, Any]:
        try:
            result = await asyncio.to_thread(
                self._execute_in_sandbox,
                code,
                df.head(max_rows).to_dict("records"),
                dataset_reference,
            )
            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            logger.error(f"E2B 执行失败: {traceback.format_exc()}")
            return {"success": False, "error": f"E2B 执行错误: {str(e)}"}

    def _execute_in_sandbox(self, code: str, records: list[dict], dataset_reference: Optional[str] = None) -> Any:
        if not E2B_API_KEY:
            raise RuntimeError("未配置 E2B_API_KEY，Pandas 分析沙箱不可用。")
        records_json = json.dumps(records, ensure_ascii=False)
        ref_json = json.dumps(dataset_reference or "", ensure_ascii=False)
        records_payload = base64.b64encode(records_json.encode("utf-8")).decode("ascii")
        ref_payload = base64.b64encode(ref_json.encode("utf-8")).decode("ascii")
        wrapped_code = f"""
import json
import pandas as pd
import base64
from io import BytesIO
from pathlib import Path

records = json.loads(base64.b64decode('{records_payload}').decode('utf-8'))
dataset_reference = json.loads(base64.b64decode('{ref_payload}').decode('utf-8'))
current_file_path = dataset_reference
current_file_name = Path(dataset_reference).name if dataset_reference else ''
df = pd.DataFrame(records)

{code}

def _normalize_result(value):
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient='records')
    if isinstance(value, pd.Series):
        return value.to_dict()
    return value

print('__RESULT__=' + json.dumps(_normalize_result(result), ensure_ascii=False))
"""

        with Sandbox() as sandbox:
            execution = sandbox.run_code(wrapped_code, timeout=float(self.timeout))

        exec_error = getattr(execution, "error", None)
        if exec_error:
            stderr_text = self._collect_execution_text(getattr(execution, "stderr", None))
            raise RuntimeError(f"{exec_error}{(' | stderr: ' + stderr_text) if stderr_text else ''}")

        output_text = self._collect_execution_output(execution)
        clean_output_text = self._clean_output_text(output_text)
        result_match = re.search(r"^__RESULT__=(.*)$", output_text, flags=re.MULTILINE)
        if result_match:
            result_raw = result_match.group(1).strip()
            try:
                parsed_result = json.loads(result_raw)
            except Exception:
                parsed_result = result_raw
            payload: Dict[str, Any] = {
                "__data__": parsed_result,
                "__chart_data__": None,
                "__sandbox_output__": clean_output_text,
            }
            return payload

        results = getattr(execution, "results", None)
        if results is not None:
            parsed = self._extract_from_results(results)
            if parsed is not None:
                return {
                    "__data__": parsed,
                    "__chart_data__": None,
                    "__sandbox_output__": clean_output_text,
                }

        final_text = output_text.strip()
        if self._is_placeholder_result_text(final_text):
            return {
                "__data__": None,
                "__chart_data__": None,
                "__sandbox_output__": clean_output_text,
            }
        return {
            "__data__": final_text,
            "__chart_data__": None,
            "__sandbox_output__": clean_output_text,
        }

    def _collect_execution_output(self, execution: Any) -> str:
        chunks: list[str] = []

        if isinstance(execution, dict):
            for key in ("stdout", "output", "text"):
                value = execution.get(key)
                if value:
                    chunks.append(str(value))

        for attr in ("stdout", "output", "text"):
            value = getattr(execution, attr, None)
            if value:
                chunks.append(str(value))

        logs = getattr(execution, "logs", None)
        if logs is not None:
            if isinstance(logs, dict):
                for key in ("stdout", "stderr"):
                    value = logs.get(key)
                    if value:
                        if isinstance(value, list):
                            chunks.extend(str(x) for x in value)
                        else:
                            chunks.append(str(value))
            else:
                for key in ("stdout", "stderr"):
                    value = getattr(logs, key, None)
                    if value:
                        if isinstance(value, list):
                            chunks.extend(str(x) for x in value)
                        else:
                            chunks.append(str(value))

        if not chunks:
            chunks.append(str(execution))

        return "\n".join(chunks)

    def _collect_execution_text(self, items: Any) -> str:
        if items is None:
            return ""
        if isinstance(items, str):
            return items
        if isinstance(items, list):
            parts: list[str] = []
            for item in items:
                line = getattr(item, "line", None)
                if line is not None:
                    parts.append(str(line))
                    continue
                text = getattr(item, "text", None)
                if text is not None:
                    parts.append(str(text))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(items)

    def _clean_output_text(self, output_text: str) -> str:
        """移除内部标记行，保留可读的沙箱输出。"""
        if not output_text:
            return ""
        lines = [
            line
            for line in output_text.splitlines()
            if not line.startswith("__RESULT__=") and not line.startswith("__CHART__=")
        ]
        return "\n".join(lines).strip()

    def _extract_from_results(self, results: Any) -> Any:
        try:
            if isinstance(results, list) and results:
                main_result = None
                for item in results:
                    if getattr(item, "is_main_result", False):
                        main_result = item
                        break
                last = main_result or results[-1]

                for attr in ("json", "data", "text", "value"):
                    if hasattr(last, attr):
                        value = getattr(last, attr)
                        if value is None:
                            continue
                        normalized_value = self._normalize_extracted_value(value)
                        if normalized_value is not None:
                            return normalized_value
                last_text = str(last).strip()
                return self._normalize_extracted_value(last_text)
            return None
        except Exception:
            return None

    def _normalize_extracted_value(self, value: Any) -> Any:
        """将沙箱结果归一化为前端可展示的数据，过滤 Result()/Figure 等占位文本。"""
        if value is None:
            return None

        if isinstance(value, (dict, list, int, float, bool)):
            return value

        text = str(value).strip()
        if not text:
            return None

        unwrapped = self._unwrap_result_wrapper(text)
        candidate = unwrapped if unwrapped is not None else text

        if self._is_placeholder_result_text(candidate):
            return None

        try:
            return json.loads(candidate)
        except Exception:
            return candidate

    def _unwrap_result_wrapper(self, text: str) -> Optional[str]:
        """解包 e2b/jupyter 形如 Result(...) 的文本包装。"""
        match = re.match(r"^Result\((?P<body>[\s\S]*)\)$", (text or "").strip())
        if not match:
            return None
        return match.group("body").strip()

    def _is_placeholder_result_text(self, text: str) -> bool:
        """判断沙箱返回的占位文本，避免前端展示对象repr。"""
        normalized = (text or "").strip()
        if not normalized:
            return True

        unwrapped = self._unwrap_result_wrapper(normalized)
        if unwrapped is not None:
            if not unwrapped:
                return True
            normalized = unwrapped

        if re.match(r"^<Figure size .* with \d+ Axes>$", normalized):
            return True

        return False

    def _extract_chart_from_results(self, results: Any) -> Optional[str]:
        """从 execution.results 中提取 base64 PNG 图像（如果存在）。"""
        if not isinstance(results, list):
            return None

        for item in results:
            candidates: list[Any] = []

            if isinstance(item, dict):
                candidates.extend([
                    item.get("png"),
                    item.get("image"),
                    item.get("image/png"),
                    item.get("data"),
                ])
            else:
                candidates.extend([
                    getattr(item, "png", None),
                    getattr(item, "image", None),
                    getattr(item, "data", None),
                    getattr(item, "value", None),
                ])

            for candidate in candidates:
                parsed = self._extract_base64_png_from_candidate(candidate)
                if parsed:
                    return parsed

        return None

    def _extract_base64_png_from_candidate(self, candidate: Any) -> Optional[str]:
        if candidate is None:
            return None

        if isinstance(candidate, dict):
            image_png = candidate.get("image/png")
            if isinstance(image_png, str):
                return image_png.strip()
            if isinstance(image_png, bytes):
                return base64.b64encode(image_png).decode("ascii")

            for nested in candidate.values():
                parsed = self._extract_base64_png_from_candidate(nested)
                if parsed:
                    return parsed
            return None

        if isinstance(candidate, bytes):
            return base64.b64encode(candidate).decode("ascii")

        if isinstance(candidate, str):
            text = candidate.strip()
            if text.startswith("data:image/png;base64,"):
                return text.split(",", 1)[1].strip()
            if text.startswith("iVBOR") and re.match(r"^[A-Za-z0-9+/=\n\r]+$", text):
                return text.replace("\n", "").replace("\r", "")
            return None

        return None


class AnalysisRequest(BaseModel):
    """数据分析请求"""
    
    dataset_reference: str = Field(..., description="当前文件路径")
    analysis_query: str = Field(..., description="自然语言分析请求如'按类别计算平均价格'")
    user_instruction: Optional[str] = Field(None, description="用户的额外指示")


class AnalysisResult(BaseModel):
    """分析结果"""
    
    status: str = Field(..., description="执行状态: success/error")
    data: Any = Field(None, description="分析结果数据(表格/数组等)")
    chart_data: Optional[Any] = Field(None, description="图表数据(base64图片或结构化图表数据)")
    text_summary: Optional[str] = Field(None, description="文本摘要")
    generated_code: Optional[str] = Field(None, description="生成的Pandas代码")
    sandbox_output: Optional[str] = Field(None, description="沙箱运行原始输出")
    error_message: Optional[str] = Field(None, description="错误信息")
    execution_time: float = Field(0.0, description="执行耗时(秒)")


class PandasAnalyzer:
    """
    Pandas数据分析器
    - 接收数据集引用和自然语言查询
    - 利用LLM生成Pandas代码
    - 在沙箱环境执行代码
    - 返回结构化结果
    """
    
    def __init__(self):
        self.sandbox = PandasSandboxExecutor()
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            from langchain_openai import ChatOpenAI

            if not API_KEY:
                raise ValueError("未配置 API_KEY")

            return ChatOpenAI(
                api_key=API_KEY,
                base_url=settings.llm_base_url,
                model=settings.llm_generation_model_name or settings.llm_model_name,
                temperature=0.0
            )
        except Exception as e:
            logger.warning(f"LLM客户端初始化失败: {e}, 将使用模拟求解器")
            return None
    
    async def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        """
        执行分析流程
        
        Args:
            request: 分析请求
            
        Returns:
            分析结果
        """
        import time
        start_time = time.time()
        
        try:
            resolved_reference = await self._resolve_file_reference(request.dataset_reference)
            if not resolved_reference:
                return AnalysisResult(
                    status="error",
                    error_message=f"无法解析数据集引用: {request.dataset_reference}"
                )

            df = await self._load_from_file(resolved_reference)
            if df is None or df.empty:
                return AnalysisResult(
                    status="error",
                    error_message=f"无法加载数据集: {request.dataset_reference}"
                )

            mode = await self._decide_response_mode(
                df=df,
                analysis_query=request.analysis_query,
                user_instruction=request.user_instruction,
            )

            if mode == "direct_answer":
                direct_answer = await self._answer_directly_from_content(
                    df=df,
                    analysis_query=request.analysis_query,
                    user_instruction=request.user_instruction,
                )
                execution_time = time.time() - start_time
                return AnalysisResult(
                    status="success",
                    data=direct_answer,
                    chart_data=None,
                    text_summary="直接基于文件内容回答（未执行代码）",
                    generated_code="",
                    sandbox_output="direct_answer 模式：未执行沙箱代码",
                    execution_time=execution_time,
                )
            
            pandas_code = await self._generate_code(
                df=df,
                analysis_query=request.analysis_query,
                user_instruction=request.user_instruction
            )
            
            if not pandas_code:
                return AnalysisResult(
                    status="error",
                    error_message="代码生成失败"
                )
            
            execution_result = await self.sandbox.execute(
                pandas_code,
                df,
                dataset_reference=resolved_reference,
            )
            
            if not execution_result['success']:
                return AnalysisResult(
                    status="error",
                    error_message=execution_result['error'],
                    generated_code=pandas_code
                )
            
            result_data = execution_result['result']

            sandbox_chart_data = None
            sandbox_output = None
            if isinstance(result_data, dict) and "__data__" in result_data:
                sandbox_output = result_data.get("__sandbox_output__")
                result_data = result_data.get("__data__")
            
            processed_result = await self._process_result(result_data, df)
            
            execution_time = time.time() - start_time
            
            return AnalysisResult(
                status="success",
                data=processed_result.get('data'),
                chart_data=processed_result.get('chart_data'),
                text_summary=processed_result.get('text_summary'),
                generated_code=pandas_code,
                sandbox_output=sandbox_output,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"分析失败: {traceback.format_exc()}")
            return AnalysisResult(
                status="error",
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    async def _decide_response_mode(
        self,
        df: pd.DataFrame,
        analysis_query: str,
        user_instruction: Optional[str] = None,
    ) -> str:
        """判断当前请求应直接回答还是走代码分析。"""
        if self.llm_client is None:
            return self._decide_response_mode_fallback(analysis_query)

        try:
            schema = self._get_dataframe_schema(df)
            prompt = f"""你是一个数据问答路由器，只输出JSON。

任务：判断用户请求更适合：
1) direct_answer：直接根据文件内容回答，不执行代码
2) code_analysis：需要统计/聚合/计算/排序/图表等分析，应该生成并执行Pandas代码

数据概况：
- 列名: {schema['columns']}
- 形状: {schema['shape']}
- 样本: {schema['sample']}

用户请求: {analysis_query}
用户补充: {user_instruction or ''}

输出格式（必须是JSON，不要其它文本）：
{{"mode":"direct_answer|code_analysis","reason":"简短原因"}}
"""
            response = await asyncio.to_thread(self.llm_client.invoke, prompt)
            content = (response.content or "").strip()
            json_text = self._extract_first_json_object(content)
            parsed = json.loads(json_text) if json_text else {}
            mode = str(parsed.get("mode", "")).strip().lower()
            if mode in {"direct_answer", "code_analysis"}:
                return mode
            return self._decide_response_mode_fallback(analysis_query)
        except Exception as e:
            logger.debug(f"模式判定失败，使用规则兜底: {e}")
            return self._decide_response_mode_fallback(analysis_query)

    def _decide_response_mode_fallback(self, analysis_query: str) -> str:
        """基于关键词的路由兜底。"""
        query = (analysis_query or "").lower()
        analysis_keywords = [
            "统计", "平均", "均值", "求和", "总和", "分组", "趋势", "占比", "同比", "环比",
            "最大", "最小", "中位", "方差", "标准差", "排序", "top", "count", "sum", "mean",
            "group", "pivot", "相关", "回归", "聚类", "图", "图表", "柱状", "折线", "饼图"
        ]
        return "code_analysis" if any(k in query for k in analysis_keywords) else "direct_answer"

    async def _answer_directly_from_content(
        self,
        df: pd.DataFrame,
        analysis_query: str,
        user_instruction: Optional[str] = None,
    ) -> str:
        """直接基于当前文件内容回答，不执行代码。"""
        context = self._build_direct_answer_context(df)
        if self.llm_client is None:
            return f"已读取当前文件内容。问题：{analysis_query}\n\n摘要：{context[:400]}"

        prompt = f"""你是一个文档问答助手，请只基于给定文件内容回答。

要求：
1. 不要编造文件中不存在的信息。
2. 若信息不足，明确说明“文件内容不足以回答”。
3. 回答简洁，优先中文。

用户问题：{analysis_query}
用户补充：{user_instruction or ''}

文件内容（节选）：
{context}
"""
        response = await asyncio.to_thread(self.llm_client.invoke, prompt)
        return (response.content or "").strip() or "文件内容不足以回答该问题。"

    def _build_direct_answer_context(self, df: pd.DataFrame, max_chars: int = 7000) -> str:
        """构建用于直接回答的文件内容上下文。"""
        try:
            if 'content' in df.columns:
                lines = [str(v) for v in df['content'].dropna().astype(str).tolist() if str(v).strip()]
                text = "\n".join(lines)
                return text[:max_chars]

            head_df = df.head(30)
            preview = head_df.to_csv(index=False)
            schema = self._get_dataframe_schema(df)
            text = (
                f"列名: {schema['columns']}\n"
                f"数据类型: {schema['dtypes']}\n"
                f"数据规模: {schema['shape']}\n"
                f"前30行CSV:\n{preview}"
            )
            return text[:max_chars]
        except Exception:
            return ""

    def _extract_first_json_object(self, text_content: str) -> Optional[str]:
        """从文本中提取第一个JSON对象字符串。"""
        if not text_content:
            return None
        text_content = text_content.strip()
        if text_content.startswith("{") and text_content.endswith("}"):
            return text_content

        match = re.search(r"\{[\s\S]*?\}", text_content)
        return match.group(0) if match else None
    
    async def _load_dataset(self, dataset_reference: str) -> Optional[pd.DataFrame]:
        """
        加载数据集（仅支持文件）。
        """
        try:
            resolved_reference = await self._resolve_file_reference(dataset_reference)
            if not resolved_reference:
                return None

            return await self._load_from_file(resolved_reference)
            
        except Exception as e:
            logger.error(f"加载数据集失败 {dataset_reference}: {e}")
            return None

    async def _resolve_file_reference(self, dataset_reference: str) -> Optional[str]:
        """将数据集引用标准化为可读取文件路径，兼容 doc_id 与多种路径格式。"""
        ref = str(dataset_reference or "").strip()
        if not ref:
            return None

        if len(ref) >= 2 and ref[0] == ref[-1] and ref[0] in {"\"", "'"}:
            ref = ref[1:-1].strip()
        if ref.startswith("file://"):
            ref = ref[7:]
        ref = unquote(ref)

        if ref.isdigit():
            mapped_from_doc = await self._resolve_doc_id_to_file_path(ref)
            if not mapped_from_doc:
                logger.warning(f"dataset_reference 为 doc_id 但未找到文件路径: {ref}")
                return None
            ref = mapped_from_doc

        normalized = ref.strip().replace("\\", "/")
        resolved_candidate = _resolve_local_file_path(ref)
        if resolved_candidate:
            return resolved_candidate

        if normalized.startswith('/data/files/') or normalized.startswith('\\data\\files\\'):
            rel = normalized.replace('\\', '/').split('/data/files/', 1)[-1]
            mapped = Path(settings.upload_dir) / rel
            if mapped.exists():
                return str(mapped)

        if normalized.startswith('/data/uploads/') or normalized.startswith('\\data\\uploads\\'):
            mapped = Path(settings.upload_dir) / Path(normalized).name
            if mapped.exists():
                return str(mapped)

        upload_candidate = Path(settings.upload_dir) / Path(normalized).name
        if upload_candidate.exists():
            return str(upload_candidate)

        return None

    async def _resolve_doc_id_to_file_path(self, doc_id: str) -> Optional[str]:
        """根据文档ID查询文件路径，兼容前端仅传 doc_id 的历史行为。"""
        try:
            document_id = int(doc_id)
            async with AsyncSessionLocal() as session:
                stmt = select(Document.file_path).where(
                    Document.doc_id == document_id,
                    Document.is_deleted == "F",
                )
                result = await session.execute(stmt)
                file_path = result.scalar_one_or_none()
                return str(file_path).strip() if file_path else None
        except Exception as e:
            logger.warning(f"通过 doc_id 解析文件路径失败 ({doc_id}): {e}")
            return None
    
    async def _load_from_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """从文件加载数据"""
        try:
            resolved_path = _resolve_local_file_path(file_path) or file_path
            path = Path(resolved_path)
            if not path.exists():
                logger.debug(f"文件不存在: {file_path}")
                return None

            suffix = path.suffix.lower()

            if suffix == '.csv':
                df = pd.read_csv(path)
            elif suffix in {'.xlsx', '.xls'}:
                df = pd.read_excel(path)
            elif suffix == '.json':
                df = pd.read_json(path)
            elif suffix == '.parquet':
                df = pd.read_parquet(path)
            elif suffix in {'.txt', '.md'}:
                content = path.read_text(encoding='utf-8', errors='ignore')
                df = pd.DataFrame({'content': [line for line in content.splitlines() if line.strip()]})
            elif suffix == '.docx':
                from docx import Document as DocxDocument

                doc = DocxDocument(str(path))
                lines = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
                df = pd.DataFrame({'content': lines})
            elif suffix == '.pdf':
                from pypdf import PdfReader

                reader = PdfReader(str(path))
                texts: list[str] = []
                for page in reader.pages:
                    page_text = page.extract_text() or ''
                    if page_text.strip():
                        texts.extend([line for line in page_text.splitlines() if line.strip()])
                df = pd.DataFrame({'content': texts})
            else:
                return None
            
            logger.info(f"从文件加载: {file_path}: {len(df)} 行")
            return df
            
        except Exception as e:
            logger.debug(f"从文件加载失败: {e}")
            return None
    
    async def _generate_code(
        self,
        df: pd.DataFrame,
        analysis_query: str,
        user_instruction: Optional[str] = None
    ) -> Optional[str]:
        """
        利用LLM生成Pandas代码
        """
        try:
            df_schema = self._get_dataframe_schema(df)
            prompt = self._build_code_prompt(df_schema, analysis_query, user_instruction)
            
            if self.llm_client is None:
                return self._generate_code_fallback(analysis_query, df)
            
            response = self.llm_client.invoke(prompt)
            code = self._extract_code_from_response(response.content)
            if not code:
                return self._generate_code_fallback(analysis_query, df)

            if self._contains_fabricated_dataset_code(code):
                logger.warning("检测到伪造数据集代码，已回退到基于当前文件的规则代码")
                return self._generate_code_fallback(analysis_query, df)
            
            logger.info(f"生成Pandas代码: {len(code)} 个字符")
            return code
            
        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            return None
    
    def _get_dataframe_schema(self, df: pd.DataFrame) -> dict:
        """获取DataFrame的schema信息"""
        return {
            'columns': df.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'shape': df.shape,
            'sample': df.head(3).to_dict('records')
        }
    
    def _build_code_prompt(self, schema: dict, query: str, instruction: Optional[str]) -> str:
        """构建代码生成提示词"""
        prompt = f"""您是一个数据分析专家。根据给定的DataFrame和用户请求，生成安全高效的Pandas代码。

DataFrame信息:
- 列名: {schema['columns']}
- 数据类型: {schema['dtypes']}
- 形状: {schema['shape']}
- 样本数据: {schema['sample']}

用户请求: {query}
"""
        if instruction:
            prompt += f"\n用户补充说明: {instruction}"
        
        prompt += """

要求:
1. 只使用Pandas操作，不使用其他库
2. 代码必须安全，避免危险操作
3. 返回结果应该是清晰的数据结构(列表/字典/DataFrame)
4. 不要使用外部API或网络请求
5. 输入数据已经在变量 df 中，必须直接基于 df 分析
6. 严禁重新创建或覆盖 df（如 df = pd.DataFrame(...)）
7. 严禁读取任何外部数据源（read_csv/read_excel/read_json/read_parquet/SQL）
8. 代码末尾必须给 result 赋值，且 result 不能为 None
9. 当前文件信息可通过 current_file_path 与 current_file_name 使用（由前端当前文件传入）

请只返回Python代码，使用```python```代码块包装:
"""
        return prompt

    def _contains_fabricated_dataset_code(self, code: str) -> bool:
        """检测是否存在伪造数据集或覆盖当前 df 的代码。"""
        lowered = code.lower()
        banned_patterns = [
            r"\bdf\s*=\s*pd\.dataframe\s*\(",
            r"\bdf\s*=\s*pd\.read_csv\s*\(",
            r"\bdf\s*=\s*pd\.read_excel\s*\(",
            r"\bdf\s*=\s*pd\.read_json\s*\(",
            r"\bdf\s*=\s*pd\.read_parquet\s*\(",
            r"\bread_sql\s*\(",
        ]
        return any(re.search(pattern, lowered) for pattern in banned_patterns)
    
    def _extract_code_from_response(self, response_text: str) -> Optional[str]:
        """从LLM响应中提取代码"""
        pattern = r'```python\n(.*?)\n```'
        matches = re.findall(pattern, response_text, re.DOTALL)
        
        if matches:
            return matches[0]
        
        lines = response_text.split('\n')
        code_lines = [line for line in lines if line.strip() and not line.startswith('#')]
        return '\n'.join(code_lines) if code_lines else None
    
    def _generate_code_fallback(self, query: str, df: pd.DataFrame) -> Optional[str]:
        """
        降级的代码生成 - 基于模式匹配
        """
        query_lower = query.lower()
        
        if '平均' in query_lower or 'average' in query_lower or 'mean' in query_lower:
            if '按' in query_lower:
                return 'result = df.groupby(df.columns[0]).mean(numeric_only=True).reset_index()'
            else:
                return 'result = df.mean(numeric_only=True).to_frame().T'
        
        if any(w in query_lower for w in ['计数', 'count', '行数']):
            return 'result = pd.DataFrame({"count": [len(df)]})'
        
        if '分组' in query_lower or 'group' in query_lower:
            return 'result = df.groupby(df.columns[0]).size().reset_index(name="count")'
        
        return 'result = df.head(10)'
    
    async def _process_result(self, result_data: Any, original_df: pd.DataFrame) -> dict:
        """
        后处理结果 - 转换为可视化友好的格式
        """
        processed = {}
        
        if isinstance(result_data, pd.DataFrame):
            processed['data'] = result_data.to_dict('records')
        
        elif isinstance(result_data, pd.Series):
            processed['data'] = result_data.to_dict()
        
        elif isinstance(result_data, (list, dict)):
            processed['data'] = result_data

        elif isinstance(result_data, str):
            text_value = result_data.strip()
            if self.sandbox._is_placeholder_result_text(text_value):
                text_value = ""
            processed['data'] = text_value if text_value else None
        
        elif isinstance(result_data, (int, float)):
            processed['data'] = result_data
            processed['text_summary'] = f"结果值: {result_data}"
        
        if 'text_summary' not in processed:
            processed['text_summary'] = self._generate_text_summary(result_data)
        
        return processed
    
    def _generate_chart_data(self, df: pd.DataFrame) -> Optional[dict]:
        """生成图表数据"""
        try:
            if df.empty:
                return None
            
            if len(df.columns) == 2:
                return {
                    'type': 'bar',
                    'labels': df.iloc[:, 0].astype(str).tolist(),
                    'values': df.iloc[:, 1].tolist()
                }
            
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                return {
                    'type': 'table',
                    'data': df.to_dict('records')
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"生成图表数据失败: {e}")
            return None
    
    def _generate_text_summary(self, data: Any) -> str:
        """生成文本摘要"""
        try:
            if isinstance(data, pd.DataFrame):
                return f"数据表包含 {len(data)} 行，{len(data.columns)} 列"
            elif isinstance(data, dict):
                return f"分析完成，包含 {len(data)} 个键"
            elif isinstance(data, list):
                return f"分析完成，包含 {len(data)} 个项目"
            else:
                return "分析完成"
        except:
            return "分析完成"


_analyzer_instance = None

async def get_analyzer() -> PandasAnalyzer:
    """获取全局分析器实例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = PandasAnalyzer()
    return _analyzer_instance
