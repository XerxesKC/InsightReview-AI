from __future__ import annotations
from collections.abc import Sequence
from datetime import datetime
import json
from sqlalchemy import func, or_, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import ChatSession, ChatTurn, Document, KnowledgeBase, SystemConfig
from sqlalchemy import update

def _actor_scope_clause(actor: dict[str, str]):
    user_id = actor.get("user_id", "")
    user_type = actor.get("user_type", "")
    return user_type, user_id


async def list_knowledge_bases(
    session: AsyncSession,
    *,
    actor: dict[str, str] | None = None,
    name: str | None = None,
    owner_type: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> Sequence[KnowledgeBase]:
    stmt = select(KnowledgeBase).where(KnowledgeBase.is_deleted == "F")

    if name:
        stmt = stmt.where(KnowledgeBase.name.like(f"%{name}%"))

    if owner_type:
        stmt = stmt.where(KnowledgeBase.owner_type == owner_type)

    if created_from:
        stmt = stmt.where(KnowledgeBase.created_at >= created_from)
    if created_to:
        stmt = stmt.where(KnowledgeBase.created_at <= created_to)

    if actor:
        user_type, user_id = _actor_scope_clause(actor)
        stmt = stmt.where(
            or_(
                (KnowledgeBase.owner_type == user_type) & (KnowledgeBase.owner_id == user_id),
                (KnowledgeBase.admin_id == user_id),
            )
        )
    result = await session.execute(stmt.order_by(KnowledgeBase.created_at.desc()))
    return result.scalars().all()


async def create_document(
    session: AsyncSession,
    *,
    doc_name: str,
    doc_type: str,
    doc_size: int,
    file_path: str,
    uploader_type: str,
    uploader_id: int,
    kb_id: int | None = None,
    status: str = "pending",
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> Document:
    document = Document(
        doc_name=doc_name,
        doc_type=doc_type,
        doc_size=doc_size,
        file_path=file_path,
        uploader_type=uploader_type,
        uploader_id=uploader_id,
        kb_id=kb_id,
        status=status,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


async def list_documents(
    session: AsyncSession,
    user_type: str,
    user_id: int,
    kb_id: int | None = None,
) -> Sequence[Document]:
    stmt = select(Document).where(Document.is_deleted == "F")
    if kb_id is not None:
        stmt = stmt.where(Document.kb_id == kb_id)
    stmt = stmt.where(
        or_(
            and_(
                Document.uploader_type == user_type,
                Document.uploader_id == user_id
            ),
            Document.kb_id.in_(
                select(KnowledgeBase.kb_id).where(
                    KnowledgeBase.is_deleted == "F",
                    KnowledgeBase.owner_type == user_type,
                    KnowledgeBase.owner_id == user_id,
                )
            ),
        )
    )

    result = await session.execute(stmt.order_by(Document.created_at.desc()))
    return result.scalars().all()


async def update_document(
        session: AsyncSession,
        doc_id: int,
        doc_name: str,
        doc_type: str,
        doc_size: int,
        file_path: str,
        status: str,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        kb_id: int | None = None,
):
    stmt = select(Document).where(Document.doc_id == doc_id)
    result = await session.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        return None

    document.doc_name = doc_name
    document.doc_type = doc_type
    document.doc_size = doc_size
    document.file_path = file_path
    document.status = status

    if chunk_size is not None:
        document.chunk_size = chunk_size
    if chunk_overlap is not None:
        document.chunk_overlap = chunk_overlap
    if kb_id is not None:
        document.kb_id = kb_id

    await session.commit()
    await session.refresh(document)

    return document


async def get_document_for_actor(
    session: AsyncSession,
    document_id: int,
    *,
    actor: dict[str, str],
) -> Document | None:
    user_type, user_id = _actor_scope_clause(actor)
    stmt = (
        select(Document)
        .where(Document.doc_id == document_id, Document.is_deleted == "F")
        .where(
            or_(
                (Document.uploader_type == user_type) & (Document.uploader_id == user_id),
                Document.kb_id.in_(
                    select(KnowledgeBase.kb_id).where(
                        KnowledgeBase.is_deleted == "F",
                        KnowledgeBase.owner_type == user_type,
                        KnowledgeBase.owner_id == user_id,
                    )
                ),
            )
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def soft_delete_document(
    session: AsyncSession,
    document_id: int,
) -> Document | None:
    stmt = select(Document).where(
        Document.doc_id == document_id,
        Document.is_deleted == "F"
    )
    result = await session.execute(stmt)
    document = result.scalar_one_or_none()
    if document is None:
        return None
    document.is_deleted = "T"
    await session.commit()
    return document

async def get_document_by_id(
    session: AsyncSession,
    document_id: int,
) -> Document | None:
    stmt = select(Document).where(
        Document.doc_id == document_id,
        Document.is_deleted == "F")
    result = await session.execute(stmt)
    document = result.scalar_one_or_none()
    return document

async def bind_documents_to_kb(
    session: AsyncSession, 
    doc_ids: list[int], 
    kb_id: int
) -> int:
    """
    将一批 document_id 绑定到指定的知识库 (更新 kb_id)
    """
    if not doc_ids:
        return 0
        
    stmt = (
        update(Document)
        .where(Document.doc_id.in_(doc_ids))
        .values(kb_id=kb_id)
    )
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount

def _default_session_title(query: str) -> str:
    text = (query or "新会话").strip()
    return text[:60] if text else "新会话"


async def get_chat_session_for_actor(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
) -> ChatSession | None:
    stmt = select(ChatSession).where(
        ChatSession.session_id == session_id,
        ChatSession.owner_id == owner_id,
        ChatSession.owner_type == owner_type,
        ChatSession.is_deleted.is_(False),
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_chat_session(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
    title: str | None = None,
) -> ChatSession:
    record = await get_chat_session_for_actor(
        session,
        owner_id=owner_id,
        owner_type=owner_type,
        session_id=session_id,
    )
    if record is not None:
        return record

    record = ChatSession(
        session_id=session_id,
        owner_id=owner_id,
        owner_type=owner_type,
        title=title or "新会话",
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def create_chat_turn(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
    query: str,
    answer: str,
    input_type: str = "text",
    ocr_text: str | None = None,
    turn_no: int | None = None,
    rewritten_query: str | None = None,
    sources: list[dict[str, object]] | None = None,
    is_active: bool = True,
    tokens: int = 0,
) -> ChatTurn:
    session_record = await get_or_create_chat_session(
        session,
        owner_id=owner_id,
        owner_type=owner_type,
        session_id=session_id,
        title=_default_session_title(query),
    )
    if turn_no is None:
        turn_no = await get_next_chat_turn_no(
            session,
            owner_id=owner_id,
            owner_type=owner_type,
            session_id=session_id,
        )

    record = ChatTurn(
        session_id=session_id,
        turn_no=turn_no,
        query=query,
        input_type=input_type,
        ocr_text=ocr_text,
        answer=answer,
        rewritten_query=rewritten_query,
        sources=json.dumps(sources or [], ensure_ascii=False),
        is_active=is_active,
        tokens=tokens,
    )
    session.add(record)
    session_record.turn_count = max(session_record.turn_count, turn_no)
    if is_active:
        session_record.active_turn_count += 1
    if session_record.title == "新会话" and query.strip():
        session_record.title = _default_session_title(query)
    await session.commit()
    await session.refresh(record)
    return record


async def get_next_chat_turn_no(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
) -> int:
    result = await session.execute(
        select(func.max(ChatTurn.turn_no))
        .join(ChatSession, ChatSession.session_id == ChatTurn.session_id)
        .where(
            ChatTurn.session_id == session_id,
            ChatSession.owner_id == owner_id,
            ChatSession.owner_type == owner_type,
            ChatSession.is_deleted.is_(False),
        )
    )
    max_turn_no = result.scalar_one_or_none()
    return int(max_turn_no or 0) + 1


async def list_chat_turns(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
    include_inactive: bool = False,
    limit: int | None = None,
    ascending: bool = False,
) -> Sequence[ChatTurn]:
    stmt = (
        select(ChatTurn)
        .join(ChatSession, ChatSession.session_id == ChatTurn.session_id)
        .where(
            ChatTurn.session_id == session_id,
            ChatSession.owner_id == owner_id,
            ChatSession.owner_type == owner_type,
            ChatSession.is_deleted.is_(False),
        )
    )
    if not include_inactive:
        stmt = stmt.where(ChatTurn.is_active.is_(True))

    order_column = ChatTurn.turn_no.asc() if ascending else ChatTurn.created_at.desc()
    stmt = stmt.order_by(order_column)
    if limit is not None and limit > 0:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    items = list(result.scalars().all())
    if ascending:
        return items
    return items


async def get_chat_context(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
    max_turns: int,
) -> Sequence[ChatTurn]:
    stmt = (
        select(ChatTurn)
        .join(ChatSession, ChatSession.session_id == ChatTurn.session_id)
        .where(
            ChatTurn.session_id == session_id,
            ChatTurn.is_active.is_(True),
            ChatSession.owner_id == owner_id,
            ChatSession.owner_type == owner_type,
            ChatSession.is_deleted.is_(False),
        )
        .order_by(ChatTurn.turn_no.desc())
        .limit(max(max_turns, 1))
    )
    result = await session.execute(stmt)
    items = list(result.scalars().all())
    items.reverse()
    return items


async def clear_chat_context(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
) -> int:
    session_record = await get_chat_session_for_actor(
        session,
        owner_id=owner_id,
        owner_type=owner_type,
        session_id=session_id,
    )
    if session_record is None:
        return 0

    result = await session.execute(
        select(ChatTurn).where(
            ChatTurn.session_id == session_id,
            ChatTurn.is_active.is_(True),
        )
    )
    items = list(result.scalars().all())
    for item in items:
        item.is_active = False
    session_record.active_turn_count = 0
    await session.commit()
    return len(items)


async def rollback_chat_context(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
    turn_no: int,
) -> int:
    session_record = await get_chat_session_for_actor(
        session,
        owner_id=owner_id,
        owner_type=owner_type,
        session_id=session_id,
    )
    if session_record is None:
        return 0

    result = await session.execute(
        select(ChatTurn).where(
            ChatTurn.session_id == session_id,
            ChatTurn.turn_no > turn_no,
            ChatTurn.is_active.is_(True),
        )
    )
    items = list(result.scalars().all())
    for item in items:
        item.is_active = False
    session_record.active_turn_count = max(session_record.active_turn_count - len(items), 0)
    await session.commit()
    return len(items)


async def list_chat_sessions(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    include_deleted: bool = False,
) -> Sequence[ChatSession]:
    stmt = select(ChatSession).where(
        ChatSession.owner_id == owner_id,
        ChatSession.owner_type == owner_type,
    )
    if not include_deleted:
        stmt = stmt.where(ChatSession.is_deleted.is_(False))
    result = await session.execute(stmt.order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc()))
    return result.scalars().all()


async def rename_chat_session(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
    title: str,
) -> ChatSession | None:
    record = await get_chat_session_for_actor(
        session,
        owner_id=owner_id,
        owner_type=owner_type,
        session_id=session_id,
    )
    if record is None:
        return None
    record.title = title.strip() or record.title
    await session.commit()
    await session.refresh(record)
    return record


async def update_chat_session_retrieval_config(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
    retrieval_top_k: int | None = None,
    similarity_threshold: float | None = None,
) -> ChatSession | None:
    record = await get_chat_session_for_actor(
        session,
        owner_id=owner_id,
        owner_type=owner_type,
        session_id=session_id,
    )
    if record is None:
        return None

    record.retrieval_top_k = retrieval_top_k
    record.similarity_threshold = similarity_threshold
    await session.commit()
    await session.refresh(record)
    return record


async def delete_chat_session(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
) -> ChatSession | None:
    record = await get_chat_session_for_actor(
        session,
        owner_id=owner_id,
        owner_type=owner_type,
        session_id=session_id,
    )
    if record is None:
        return None

    result = await session.execute(select(ChatTurn).where(ChatTurn.session_id == session_id, ChatTurn.is_active.is_(True)))
    for item in result.scalars().all():
        item.is_active = False
    record.is_deleted = True
    record.active_turn_count = 0
    await session.commit()
    await session.refresh(record)
    return record


async def update_chat_turn_rating(
    session: AsyncSession,
    *,
    owner_id: str,
    owner_type: str,
    session_id: str,
    turn_no: int,
    rating: int,
) -> bool:
    """
    更新聊天回合评分
    
    Args:
        session: 数据库会话
        owner_id: 所有者ID
        owner_type: 所有者类型
        session_id: 会话ID
        turn_no: 回合编号
        rating: 评分值 (-1, 0, 1)
    
    Returns:
        是否更新成功
    """
    if rating not in [-1, 0, 1]:
        return False
    
    stmt = (
    update(ChatTurn)
    .where(
        ChatTurn.session_id == session_id,
        ChatTurn.turn_no == turn_no,
        ChatTurn.session_id.in_(
            select(ChatSession.session_id)
            .where(
                ChatSession.session_id == session_id,
                ChatSession.owner_id == owner_id,
                ChatSession.owner_type == owner_type,
                ChatSession.is_deleted.is_(False),
            )
        )
    )
    .values(rating=rating)
    )
    
    result = await session.execute(stmt)
    await session.commit()
    
    return result.rowcount > 0

async def upsert_system_config(session: AsyncSession, *, key: str, value: str) -> SystemConfig:
    result = await session.execute(select(SystemConfig).where(SystemConfig.config_key == key))
    config = result.scalar_one_or_none()
    if config is None:
        config = SystemConfig(config_key=key, config_value=value)
        session.add(config)
    else:
        config.config_value = value
    await session.commit()
    await session.refresh(config)
    return config


async def reject_document(
        session: AsyncSession,
        document_id: int,
) -> Document | None:
    """
    驳回文档，将文档状态改为rejected

    Args:
        session: 数据库会话
        document_id: 文档ID

    Returns:
        Document: 更新后的文档对象，如果文档不存在或状态不允许驳回则返回None
    """
    stmt = select(Document).where(
        Document.doc_id == document_id,
        Document.is_deleted == "F"
    )
    result = await session.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        return None

    if document.status == "rejected":
        return None

    if document.status == "approved":
        return None

    document.status = "rejected"
    await session.commit()
    await session.refresh(document)

    return document

async def search_documents(
        session: AsyncSession,
        *,
        actor: dict[str, str] | None = None,
        kb_id: int | None = None,
        uploader_type: str | None = None,
        uploader_id: str | None = None,
        doc_name: str | None = None,
        doc_type: str | None = None,
        status: str | None = None,
        chunk_size_min: int | None = None,
        chunk_size_max: int | None = None,
        chunk_count_min: int | None = None,
        chunk_count_max: int | None = None,
        page: int = 1,
        page_size: int = 20
) -> tuple[Sequence[Document], int]:
    """
    根据传入参数动态筛选文档

    参数:
        session: 数据库会话
        actor: 用户信息，用于权限控制
        kb_id: 知识库ID
        uploader_type: 上传者类型
        uploader_id: 上传者ID
        doc_name: 文档名称（支持模糊匹配）
        doc_type: 文档类型
        status: 文档状态
        chunk_size_min: 最小拆分块大小
        chunk_size_max: 最大拆分块大小
        chunk_count_min: 最小块数量
        chunk_count_max: 最大块数量
        page: 页码
        page_size: 每页大小

    返回:
        (文档列表, 总数量)
    """
    stmt = select(Document).where(Document.is_deleted.is_(False))

    if actor:
        user_type, user_id = _actor_scope_clause(actor)
        stmt = stmt.where(
            or_(
                (Document.uploader_type == user_type) & (Document.uploader_id == user_id),
                Document.kb_id.in_(
                    select(KnowledgeBase.kb_id).where(
                        KnowledgeBase.is_deleted.is_(False),
                        KnowledgeBase.owner_type == user_type,
                        KnowledgeBase.owner_id == user_id,
                    )
                ),
            )
        )

    if kb_id is not None:
        stmt = stmt.where(Document.kb_id == kb_id)

    if uploader_type is not None:
        if uploader_type == "__exclude_chat__":
            stmt = stmt.where(Document.uploader_type != "chat")
        else:
            stmt = stmt.where(Document.uploader_type == uploader_type)

    if uploader_id is not None:
        stmt = stmt.where(Document.uploader_id == uploader_id)

    if doc_name is not None:
        stmt = stmt.where(Document.doc_name.ilike(f"%{doc_name}%"))

    if doc_type is not None:
        stmt = stmt.where(Document.doc_type == doc_type)

    if status is not None:
        stmt = stmt.where(Document.status == status)

    if chunk_size_min is not None:
        stmt = stmt.where(Document.chunk_size >= chunk_size_min)

    if chunk_size_max is not None:
        stmt = stmt.where(Document.chunk_size <= chunk_size_max)

    if chunk_count_min is not None:
        stmt = stmt.where(Document.chunk_count >= chunk_count_min)

    if chunk_count_max is not None:
        stmt = stmt.where(Document.chunk_count <= chunk_count_max)
    from sqlalchemy import func
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(Document.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    documents = result.scalars().all()

    return documents, total



async def get_system_config_value(
    session: AsyncSession,
    *,
    key: str,
) -> str | None:
    result = await session.execute(select(SystemConfig).where(SystemConfig.config_key == key))
    config = result.scalar_one_or_none()
    return None if config is None else config.config_value


async def get_system_config_map(
    session: AsyncSession,
    *,
    keys: list[str],
) -> dict[str, str]:
    if not keys:
        return {}
    result = await session.execute(select(SystemConfig).where(SystemConfig.config_key.in_(keys)))
    rows = result.scalars().all()
    return {row.config_key: row.config_value for row in rows}


async def upsert_system_config_map(
    session: AsyncSession,
    *,
    items: dict[str, str],
) -> dict[str, str]:
    if not items:
        return {}
    for key, value in items.items():
        await upsert_system_config(session, key=key, value=value)
    return items


async def create_knowledge_base(
    session: AsyncSession,
    *,
    admin_id: str,
    name: str,
    description: str,
    owner_type: str,
    owner_id: str,
    embedding_model: str,
    chroma_collection: str,
    status: str = "active",
) -> KnowledgeBase:
    kb = KnowledgeBase(
        admin_id=admin_id,
        name=name,
        description=description,
        owner_type=owner_type,
        owner_id=owner_id,
        embedding_model=embedding_model,
        chroma_collection=chroma_collection,
    )
    session.add(kb)
    await session.commit()
    await session.refresh(kb)
    return kb


async def update_knowledge_base(
    session: AsyncSession,
    kb_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    owner_type: str | None = None,
    owner_id: str | None = None,
    embedding_model: str | None = None,
    chroma_collection: str | None = None,
) -> KnowledgeBase | None:
    kb = await session.get(KnowledgeBase, kb_id)
    if kb is None or kb.is_deleted != "F":
        return None
    if name is not None:
        kb.name = name
    if description is not None:
        kb.description = description
    if owner_type is not None:
        kb.owner_type = owner_type
    if owner_id is not None:
        kb.owner_id = owner_id
    if embedding_model is not None:
        kb.embedding_model = embedding_model
    if chroma_collection is not None:
        kb.chroma_collection = chroma_collection
    await session.commit()
    await session.refresh(kb)
    return kb


async def soft_delete_knowledge_base(
    session: AsyncSession,
    kb_id: int,
) -> KnowledgeBase | None:
    kb = await session.get(KnowledgeBase, kb_id)
    if kb is None or kb.is_deleted != "F":
        return None
    kb.is_deleted = "T"
    await session.commit()
    await session.refresh(kb)
    return kb


async def get_knowledge_base(
    session: AsyncSession,
    kb_id: int,
) -> KnowledgeBase | None:
    kb = await session.get(KnowledgeBase, kb_id)
    if kb is None or kb.is_deleted != "F":
        return None
    return kb


async def list_owners(
    session: AsyncSession,
    owner_type: str,
    keyword: str = "",
) -> list[dict[str, any]]:
    config_map = {
        "user": ("user_id", "user_name"),
        "merchant": ("merchant_id", "merchant_name"),
        "admin": ("admin_id", "admin_name")
    }

    config = config_map.get(owner_type)
    if not config:
        return []

    table_name = owner_type
    id_col, name_col = config

    from sqlalchemy import text

    query_str = f"""
    SELECT {id_col} AS id, {name_col} AS name 
    FROM `{table_name}`
    WHERE (is_deleted = 'F' OR is_deleted IS NULL)
    """

    if keyword:
        query_str += f" AND {name_col} LIKE :keyword"

    params = {"keyword": f"%{keyword}%"} if keyword else {}
    result = await session.execute(text(query_str), params)

    owners = []
    for row in result:
        owners.append({
            "id": str(row.id),  
            "name": row.name
        })

    return owners

async def check_duplicate_document(
        session: AsyncSession,
        *,
        doc_name: str,
        uploader_type: str,
        uploader_id: int,
) -> Document | None:
    stmt = (
        select(Document)
        .where(
            Document.doc_name == doc_name,
            Document.uploader_type == uploader_type,
            Document.uploader_id == uploader_id,
            Document.is_deleted == "F"
        )
        .order_by(Document.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def deprecated_document(
        session: AsyncSession,
        document_id: int,
) -> Document | None:
    stmt = select(Document).where(
        Document.doc_id == document_id,
        Document.is_deleted == "F"
    )
    result = await session.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        return None

    document.status = "deprecated"
    await session.commit()
    await session.refresh(document)

    return document

async def list_document_versions(
        session: AsyncSession,
        *,
        doc_name: str,
        uploader_type: str,
        uploader_id: int,
        current_doc_id: int | None = None,
) -> Sequence[Document]:
    stmt = (
        select(Document)
        .where(
            Document.doc_name == doc_name,
            Document.uploader_type == uploader_type,
            Document.uploader_id == uploader_id,
            Document.is_deleted == "F"
        )
        .order_by(Document.created_at.desc())
    )

    if current_doc_id is not None:
        stmt = stmt.where(Document.doc_id != current_doc_id)

    result = await session.execute(stmt)
    return result.scalars().all()

async def activate_document(
        session: AsyncSession,
        document_id: int,
) -> Document | None:
    stmt = select(Document).where(
        Document.doc_id == document_id,
        Document.is_deleted == "F"
    )
    result = await session.execute(stmt)
    document = result.scalar_one_or_none()

    if not document:
        return None

    document.status = "pending"
    await session.commit()
    await session.refresh(document)

    return document
