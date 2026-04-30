import csv
from io import StringIO
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, desc, select, func, or_, case
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.datetime_utils import to_rfc3339
from app.db.models import ChatSession, ChatTurn
from app.core.response import BaseResponse
from collections import Counter

router = APIRouter(tags=["dialogue-log"])


def _parse_time_filter(value: Optional[str], is_end: bool = False) -> Optional[datetime]:
    """解析时间筛选参数，兼容 YYYY-MM-DD / YYYY-MM-DD HH:MM:SS / ISO8601。"""
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None

    if len(raw) == 10:
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d")
            if is_end:
                dt = dt.replace(hour=23, minute=59, second=59)
            return dt
        except ValueError:
            pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    try:
        iso_text = raw.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(iso_text)
        if parsed.tzinfo is not None:
            return parsed.replace(tzinfo=None)
        return parsed
    except ValueError:
        return None



class TurnSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    turn_id: int
    turn_no: int
    query: str
    answer: str
    rewritten_query: Optional[str]
    sources: str
    created_at: str



class SessionItem(BaseModel):
    session_id: str
    owner_id: str
    owner_type: str
    title: str
    turn_count: int
    created_at: str


class SessionListData(BaseModel):
    items: List[SessionItem]
    total: int


class SessionDetail(BaseModel):
    session_id: str
    owner_id: str
    owner_type: str
    title: str
    created_at: str
    turns: List[TurnSchema]

class AnalysisResponse(BaseModel):
    hot_questions: List[dict]
    retrieval_success_rate: float
    average_response_time: float
    user_activity: List[dict]
    total_sessions: int
    total_turns: int
    

@router.get(
    "/dialogue-log/list",
    response_model=BaseResponse[SessionListData],
    summary="get_dialogue_logs          支持按用户、关键词、知识库及时间范围筛选会话列表。",
    operation_id="getDialogueLogs",
)
async def get_dialogue_logs(
    page: int = Query(1),
    page_size: int = Query(10),

    owner_id: Optional[str] = None,
    keyword: Optional[str] = None,
    kb_name: Optional[str] = None,

    start_time: Optional[str] = None,
    end_time: Optional[str] = None,

    db: AsyncSession = Depends(get_db)
):

    stmt = select(ChatSession).where(ChatSession.is_deleted == False)

    if owner_id:
        stmt = stmt.where(ChatSession.owner_id == owner_id)

    parsed_start_time = _parse_time_filter(start_time, is_end=False)
    parsed_end_time = _parse_time_filter(end_time, is_end=True)
    if parsed_start_time:
        stmt = stmt.where(ChatSession.created_at >= parsed_start_time)

    if parsed_end_time:
        stmt = stmt.where(ChatSession.created_at <= parsed_end_time)

    if keyword:
        stmt = stmt.join(ChatTurn).where(
            or_(
                ChatTurn.query.like(f"%{keyword}%"),
                ChatTurn.answer.like(f"%{keyword}%")
            )
        )

    if kb_name:
        stmt = stmt.join(ChatTurn).where(
            ChatTurn.sources.like(f"%{kb_name}%")
        )

    stmt = stmt.distinct()

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(ChatSession.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    items = [
        SessionItem(
            session_id=s.session_id,
            owner_id=s.owner_id,
            owner_type=s.owner_type,
            title=s.title,
            turn_count=s.turn_count,
            created_at=to_rfc3339(s.created_at) or ""
        )
        for s in sessions
    ]

    return BaseResponse(
        data=SessionListData(
            items=items,
            total=total
        )
    )



@router.get(
    "/dialogue-log/detail/{session_id}",
    response_model=BaseResponse[SessionDetail],
    summary="get_dialogue_detail          返回指定会话的基本信息及全部轮次明细。",
    operation_id="getDialogueDetail",
)
async def get_dialogue_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):

    stmt = select(ChatSession).where(
        ChatSession.session_id == session_id,
        ChatSession.is_deleted == False
    )

    result = await db.execute(stmt)
    session_obj = result.scalar_one_or_none()

    if not session_obj:
        return BaseResponse(code=404, msg="session not found")

    turn_stmt = select(
        ChatTurn.turn_id,
        ChatTurn.turn_no,
        ChatTurn.query,
        ChatTurn.answer,
        ChatTurn.rewritten_query,
        ChatTurn.sources,
        ChatTurn.created_at,
    ).where(
        ChatTurn.session_id == session_id
    ).order_by(ChatTurn.turn_no.asc())

    result = await db.execute(turn_stmt)
    turns = result.all()

    turn_list = [
        TurnSchema(
            turn_id=t.turn_id,
            turn_no=t.turn_no,
            query=t.query,
            answer=t.answer,
            rewritten_query=t.rewritten_query,
            sources=t.sources,
            created_at=to_rfc3339(t.created_at) or ""
        )
        for t in turns
    ]

    data = SessionDetail(
        session_id=session_obj.session_id,
        owner_id=session_obj.owner_id,
        owner_type=session_obj.owner_type,
        title=session_obj.title,
        created_at=to_rfc3339(session_obj.created_at) or "",
        turns=turn_list
    )

    return BaseResponse(data=data)

@router.get(
    "/dialogue-log/export",
    summary="export_dialogue_logs          按筛选条件导出 CSV 或 Excel 格式的对话日志文件。",
    operation_id="exportDialogueLogs",
)
async def export_dialogue_logs(
    format: str = Query("csv", enum=["csv", "excel"], description="导出格式"),
    owner_id: Optional[str] = None,
    keyword: Optional[str] = None,
    kb_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(
        ChatSession.session_id.label("session_id"),
        ChatSession.owner_id.label("owner_id"),
        ChatSession.owner_type.label("owner_type"),
        ChatSession.title.label("title"),
        ChatTurn.turn_no.label("turn_no"),
        ChatTurn.query.label("query"),
        ChatTurn.answer.label("answer"),
        ChatTurn.rewritten_query.label("rewritten_query"),
        ChatTurn.sources.label("sources"),
        ChatTurn.created_at.label("created_at"),
    ).join(
        ChatTurn, ChatSession.session_id == ChatTurn.session_id
    ).where(ChatSession.is_deleted == False)
    
    if owner_id:
        stmt = stmt.where(ChatSession.owner_id == owner_id)
    
    parsed_start_time = _parse_time_filter(start_time, is_end=False)
    parsed_end_time = _parse_time_filter(end_time, is_end=True)
    if parsed_start_time:
        stmt = stmt.where(ChatSession.created_at >= parsed_start_time)

    if parsed_end_time:
        stmt = stmt.where(ChatSession.created_at <= parsed_end_time)
    
    if keyword:
        stmt = stmt.where(
            or_(
                ChatTurn.query.like(f"%{keyword}%"),
                ChatTurn.answer.like(f"%{keyword}%")
            )
        )
    
    if kb_name:
        stmt = stmt.where(
            ChatTurn.sources.like(f"%{kb_name}%")
        )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    data = []
    for row in rows:
        sources = []
        if row.sources:
            try:
                sources_data = json.loads(row.sources)
                for source in sources_data:
                    sources.append(f"{source.get('source', '')} (相似度: {source.get('score', 0):.2f})")
            except json.JSONDecodeError:
                pass
        
        data.append({
            "会话ID": row.session_id,
            "用户ID": row.owner_id,
            "用户类型": row.owner_type,
            "会话标题": row.title,
            "轮次": row.turn_no,
            "用户问题": row.query,
            "系统回答": row.answer,
            "重写问题": row.rewritten_query or "",
            "参考来源": "\n".join(sources),
            "创建时间": row.created_at
        })
    
    if format == "csv":
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "会话ID", "用户ID", "用户类型", "会话标题", "轮次", "用户问题", 
            "系统回答", "重写问题", "参考来源", "创建时间"
        ])
        writer.writeheader()
        writer.writerows(data)
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=dialogue_logs_{start_time or ''}_{end_time or ''}.csv"
            }
        )
    else:  
        import pandas as pd
        from io import BytesIO
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='对话日志')
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=dialogue_logs_{start_time or ''}_{end_time or ''}.xlsx"
            }
        )
        
@router.get(
    "/dialogue-log/analysis",
    response_model=BaseResponse[dict],
    summary="get_dialogue_analysis          返回热门问题、检索成功率与用户活跃度等统计数据。",
    operation_id="getDialogueAnalysis",
)
async def get_dialogue_analysis(
    days: int = Query(3650),
    db: AsyncSession = Depends(get_db)
):
    start_date = datetime.now() - timedelta(days=days)
    
    turn_stmt = select(ChatTurn.query).where(ChatTurn.created_at >= start_date)
    turns_res = await db.execute(turn_stmt)
    queries = turns_res.scalars().all()
    hot_questions = [{"name": k, "value": v} for k, v in Counter(queries).most_common(10)]

    stats_stmt = select(
        func.count(ChatTurn.turn_id).label("total"),
        func.sum(
            case(
                (
                    and_(
                        ChatTurn.answer.notlike("%未检索到%"),
                        ChatTurn.answer.notlike("%超时%")
                    ), 
                    1
                ), 
                else_=0
            )
        ).label("success_count"),
        func.avg(ChatTurn.tokens).label("avg_tokens") 
    ).where(ChatTurn.created_at >= start_date)
    
    stats_res = await db.execute(stats_stmt)
    stats = stats_res.first()
    
    total_count = stats.total if stats and stats.total else 0
    success_count = stats.success_count if stats and stats.success_count else 0
    retrieval_rate = (success_count / total_count * 100) if total_count > 0 else 0

    activity_stmt = select(
        func.date(ChatTurn.created_at).label("date"),    
        func.count(ChatTurn.turn_id).label("count")      
    ).where(ChatTurn.created_at >= start_date)\
    .group_by(func.date(ChatTurn.created_at))\
    .order_by("date")

    activity_res = await db.execute(activity_stmt)
    user_activity = [{"date": str(row.date), "count": row.count} for row in activity_res.all()]
    
    return BaseResponse(data={
        "hot_questions": hot_questions,
        "retrieval_success_rate": round(retrieval_rate, 2),
        "average_response_time": round(stats.avg_tokens or 0, 2), 
        "user_activity": user_activity
    })
