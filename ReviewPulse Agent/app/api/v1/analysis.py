from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import DBSession
from app.core.datetime_utils import to_rfc3339
from app.db.models import ChatSession, ChatTurn
from app.services.pandas_analyzer import AnalysisRequest, AnalysisResult, get_analyzer

router = APIRouter(prefix="/analysis", tags=["analysis"])


class ExportRequest(BaseModel):
    format: str = Field(default="json")
    include_tokens: bool = True


@router.get(
    "/logs",
    summary="get_logs          分页读取对话轮次日志并返回会话归属信息。",
    operation_id="getAnalysisLogs",
)
async def get_logs(session: DBSession, limit: int = 20):
    stmt = (
        select(ChatTurn, ChatSession)
        .join(ChatSession, ChatSession.session_id == ChatTurn.session_id)
        .order_by(ChatTurn.created_at.desc())
        .limit(max(limit, 0) or 20)
    )
    result = await session.execute(stmt)
    rows = result.all()

    def _parse_sources(raw_sources: str) -> list[dict]:
        try:
            parsed = json.loads(raw_sources or "[]")
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []

    return {
        "items": [
            {
                "turn_id": turn.turn_id,
                "owner_id": chat_session.owner_id,
                "owner_type": chat_session.owner_type,
                "session_id": turn.session_id,
                "turn_no": turn.turn_no,
                "query": turn.query,
                "answer": turn.answer,
                "rewritten_query": turn.rewritten_query,
                "sources": _parse_sources(turn.sources),
                "is_active": turn.is_active,
                "tokens": turn.tokens,
                "created_at": to_rfc3339(turn.created_at),
            }
            for turn, chat_session in rows
        ]
    }


@router.post(
    "/export",
    summary="export_logs          导出日志接口占位实现，返回导出参数回显。",
    operation_id="exportAnalysisLogs",
)
async def export_logs(payload: ExportRequest):
    return {
        "status": "ready",
        "format": payload.format,
        "message": "脚手架阶段返回占位导出结果。",
        "include_tokens": payload.include_tokens,
    }


@router.post(
    "/pandas-analyze",
    summary="analyze_data_with_pandas          根据数据集引用和自然语言指令执行分析并返回结果。",
    operation_id="analyzeDataWithPandas",
    responses={400: {"description": "分析请求参数错误"}, 500: {"description": "分析服务内部错误"}},
)
async def analyze_data_with_pandas(request: AnalysisRequest) -> AnalysisResult:
    """
    Pandas数据分析接口
    
    接收:
        - dataset_reference: 当前文件路径
        - analysis_query: 自然语言分析请求
        - user_instruction: 可选的用户补充说明
    
    返回:
        - 分析结果(数据、图表、摘要等)
        - 生成的代码(用于审计)
        - 执行统计信息
    
    示例:
        POST /api/v1/analysis/pandas-analyze
        {
            "dataset_reference": "sales_data.csv",
            "analysis_query": "按地区计算总销售额",
            "user_instruction": "使用2024年数据"
        }
    """
    try:
        analyzer = await get_analyzer()
        result = await analyzer.analyze(request)
        
        if result.status == "error":
            raise HTTPException(
                status_code=400,
                detail=result.error_message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"分析服务内部错误: {str(e)}"
        )


@router.get(
    "/pandas-analyze/templates",
    summary="get_analysis_templates          返回前端可复用的常见分析模板与示例。",
    operation_id="getAnalysisTemplates",
)
async def get_analysis_templates():
    """
    获取分析模板和示例查询
    
    返回常见的分析模式供前端选择
    """
    return {
        "templates": [
            {
                "id": "avg_by_category",
                "name": "按类别计算平均值",
                "query_template": "按{column1}计算{column2}的平均值",
                "example": "按category计算price的平均值",
                "icon": "chart-line"
            },
            {
                "id": "sum_by_category",
                "name": "按类别求和",
                "query_template": "按{column1}计算{column2}的总和",
                "example": "按region计算sales的总和",
                "icon": "plus-circle"
            },
            {
                "id": "count",
                "name": "计数统计",
                "query_template": "统计{column}的出现次数",
                "example": "统计status的出现次数",
                "icon": "bar-chart"
            },
            {
                "id": "correlation",
                "name": "相关性分析",
                "query_template": "{column1}和{column2}的相关系数",
                "example": "price和rating的相关系数",
                "icon": "git-branch"
            },
            {
                "id": "trend",
                "name": "趋势分析",
                "query_template": "按{time_column}统计{metric}的趋势",
                "example": "按日期统计销售额的趋势",
                "icon": "trending-up"
            },
            {
                "id": "top_n",
                "name": "Top N排序",
                "query_template": "按{column}排序找出前N个记录",
                "example": "按销售额排序找出Top10的商品",
                "icon": "arrow-up"
            }
        ]
    }

