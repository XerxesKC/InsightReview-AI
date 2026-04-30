from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
import asyncio
import os

from arq import create_pool
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, Union, List, Any, Dict
from fastapi.responses import Response
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.db.crud import get_system_config_map, search_documents, get_document_for_actor, reject_document, get_document_by_id
from app.db.models import Document
from app.core.config import get_settings
from app.core.datetime_utils import to_rfc3339
from app.core.response import BaseResponse
from app.rag.vector_store import get_vector_store
from app.rag.embeddings import resolve_embedding_device, resolve_local_embedding_model_path
from app.services.data_pipeline.cleaner import CleaningPipeline
from app.services.data_pipeline.extractors import ExtractorFactory
from app.services.data_pipeline.text_splitter import TextSplitter
from app.services.etl_pipeline import DocumentTextSplitter, extract_text_from_docx, clean_text, extract_text_from_pdf,\
    build_document_chunks, get_absolute_path, extract_text_from_csv, extract_text_from_markdown

from flask import current_app

from app.services.file_handler import read_file_bytes
from app.worker.settings import WorkerSettings
from app.worker.tasks import generate_document_embeddings

router = APIRouter(prefix="/admin", tags=["document"])


def _resolve_document_file_path(file_path: str | None) -> str | None:
    if not file_path:
        return None

    raw_path = Path(file_path)
    if raw_path.is_absolute():
        return str(raw_path)

    module_path = Path(__file__).resolve()
    candidates = [
        Path.cwd() / raw_path,
        module_path.parents[3] / raw_path,
        module_path.parents[4] / raw_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(candidates[-1])


class DocumentItem(BaseModel):
    doc_id: int
    kb_id: Optional[int] = None
    doc_name: Optional[str] = None
    doc_type: Optional[str] = None
    doc_size: Optional[int] = None
    status: Optional[str] = None
    uploader_type: Optional[str] = None
    uploader_id: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DocumentSearchResult(BaseModel):
    items: List[DocumentItem]
    total: int
    page: int
    page_size: int
    total_pages: Optional[int] = None


class DocumentDetailData(BaseModel):
    doc_id: int
    kb_id: Optional[int] = None
    doc_name: Optional[str] = None
    doc_type: Optional[str] = None
    doc_size: Optional[int] = None
    status: Optional[str] = None
    uploader_type: Optional[str] = None
    uploader_id: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunk_count: Optional[int] = None
    file_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    content: Optional[str] = None


class ChunkPreviewItem(BaseModel):
    chunk_index: int
    content: str
    length: int
    start_preview: str


class PreviewChunksData(BaseModel):
    document_id: int
    document_name: Optional[str] = None
    chunk_size: int
    chunk_overlap: int
    total_chunks: int
    chunks: List[ChunkPreviewItem]
    stats: Dict[str, Any]


class GenerateVectorsData(BaseModel):
    doc_id: int
    doc_name: Optional[str] = None
    chunks_count: int
    vectors_count: int
    vector_dimension: int
    target_index: str
    vectors: Any


class ApproveDocumentData(BaseModel):
    doc_id: int
    doc_name: Optional[str] = None
    kb_id: Optional[int] = None
    uploader_type: str
    uploader_id: str
    chunks_count: int
    vectors_count: int
    vector_dimension: int
    target_index: str
    vectors_inserted: int
    vector_collection: str
    status: str


class RejectDocumentData(BaseModel):
    doc_id: int
    doc_name: Optional[str] = None
    status: str


class IntelligentPreviewChunkItem(BaseModel):
    chunk_id: str
    chunk_index: int
    content: str
    length: int
    start_preview: str
    document_id: int
    source_type: str
    source_location: str


class IntelligentPreviewData(BaseModel):
    document_id: int
    document_name: Optional[str] = None
    chunk_size: int
    chunk_overlap: int
    splitter_type: str
    similarity_threshold: float
    total_chunks: int
    chunks: List[IntelligentPreviewChunkItem]
    stats: Dict[str, Any]
    extraction_count: int
    cleaning_count: int


@router.get(
    "/doc-workbench/search",
    summary="search_documents_api          按条件分页查询文档，返回工作台列表数据。",
    operation_id="searchDocumentWorkbench",
    responses={500: {"description": "搜索文档失败"}},
)
async def search_documents_api(
        session: DBSession,
        user: CurrentUser,
        kb_id: Optional[int] = Query(None, description="知识库ID"),
        uploader_type: Optional[str] = Query(None, description="上传者类型"),
        uploader_id: Optional[str] = Query(None, description="上传者ID"),
        doc_name: Optional[str] = Query(None, description="文档名称（模糊匹配）"),
        doc_type: Optional[str] = Query(None, description="文档类型"),
        status: Optional[str] = Query(None, description="文档状态"),
        chunk_size_min: Optional[int] = Query(None, description="最小拆分块大小"),
        chunk_size_max: Optional[int] = Query(None, description="最大拆分块大小"),
        chunk_count_min: Optional[int] = Query(None, description="最小块数量"),
        chunk_count_max: Optional[int] = Query(None, description="最大块数量"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页大小")
):
    """
    根据传入参数查询文档 (文档工作台搜索接口)
    """
    try:
        effective_uploader_type = uploader_type
        if uploader_type is None:
            effective_uploader_type = "__exclude_chat__"

        documents, total = await search_documents(
            session,
            actor=None,  
            kb_id=kb_id,
            uploader_type=effective_uploader_type,
            uploader_id=uploader_id,
            doc_name=doc_name,
            doc_type=doc_type,
            status=status,
            chunk_size_min=chunk_size_min,
            chunk_size_max=chunk_size_max,
            chunk_count_min=chunk_count_min,
            chunk_count_max=chunk_count_max,
            page=page,
            page_size=page_size
        )

        result_data = {
            "items": [
                {
                    "doc_id": item.doc_id,
                    "kb_id": item.kb_id,
                    "doc_name": item.doc_name,
                    "doc_type": item.doc_type,
                    "doc_size": item.doc_size,
                    "status": item.status,
                    "uploader_type": item.uploader_type,
                    "uploader_id": item.uploader_id,
                    "chunk_size": item.chunk_size,
                    "chunk_overlap": item.chunk_overlap,
                    "chunk_count": item.chunk_count,
                    "created_at": to_rfc3339(item.created_at),
                    "updated_at": to_rfc3339(item.updated_at),
                }
                for item in documents
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size  
        }

        return BaseResponse(data=result_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索文档失败: {str(e)}"
        )


@router.get(
    "/documents/pending",
    summary="get_pending_documents          分页获取状态为 pending 的文档。",
    operation_id="getPendingDocuments",
    responses={500: {"description": "获取待审核文档失败"}},
)
async def get_pending_documents(
        session: DBSession,
        user: CurrentUser,
        kb_id: Optional[int] = Query(None, description="知识库ID"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页大小")
):
    """
    获取待审核文档列表
    """
    try:
        documents, total = await search_documents(
            session,
            actor=None,  
            kb_id=kb_id,
            uploader_type="__exclude_chat__",  
            status="pending",
            page=page,
            page_size=page_size
        )

        result_data = {
            "items": [
                {
                    "doc_id": item.doc_id,
                    "kb_id": item.kb_id,
                    "doc_name": item.doc_name,
                    "doc_type": item.doc_type,
                    "doc_size": item.doc_size,
                    "status": item.status,
                    "uploader_type": item.uploader_type,
                    "uploader_id": item.uploader_id,
                    "chunk_size": item.chunk_size,
                    "chunk_overlap": item.chunk_overlap,
                    "chunk_count": item.chunk_count,
                    "created_at": to_rfc3339(item.created_at),
                }
                for item in documents
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }

        return BaseResponse(data=result_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取待审核文档失败: {str(e)}"
        )

@router.get(
    "/documents/{document_id}",
    summary="get_document_detail          返回文档基础信息与可读取的文本内容。",
    operation_id="getDocumentDetail",
    responses={404: {"description": "文档不存在"}, 500: {"description": "获取文档详情失败"}},
)
async def get_document_detail(
    document_id: int,
    session: DBSession,
    user: CurrentUser
):
    """
    获取文档详情
    """
    try:
        stmt = select(Document).where(Document.doc_id == document_id, Document.is_deleted.is_(False))
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()
        print(document)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )

        document_content = ""
        try:
            file_path = _resolve_document_file_path(document.file_path)
            if file_path and os.path.exists(file_path):
                file_ext = os.path.splitext(file_path)[1].lower()

                if file_ext == '.txt':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        document_content = f.read()
                elif file_ext in ['.docx', '.doc']:
                    splitter = DocumentTextSplitter()
                    from docx import Document as DocxDocument
                    doc = DocxDocument(file_path)
                    full_text = []
                    for paragraph in doc.paragraphs:
                        full_text.append(paragraph.text)
                    document_content = '\n'.join(full_text)
                elif file_ext == '.pdf':
                    splitter = DocumentTextSplitter()
                    document_content = f"PDF文件内容解析需要专门的PDF解析库。文件路径: {file_path}"
                else:
                    document_content = f"不支持的文件类型: {file_ext}"

                if document_content:
                    document_content = clean_text(document_content)
            else:
                document_content = "文档文件不存在或路径无效111"
        except Exception as file_error:
            document_content = f"读取文档内容失败: {str(file_error)}"

        result_data = {
            "doc_id": document.doc_id,
            "kb_id": document.kb_id,
            "doc_name": document.doc_name,
            "doc_type": document.doc_type,
            "doc_size": document.doc_size,
            "status": document.status,
            "uploader_type": document.uploader_type,
            "uploader_id": document.uploader_id,
            "chunk_size": document.chunk_size,
            "chunk_overlap": document.chunk_overlap,
            "chunk_count": document.chunk_count,
            "file_path": document.file_path,
            "created_at": to_rfc3339(document.created_at),
            "updated_at": to_rfc3339(document.updated_at),
            "content": document_content
        }

        return BaseResponse(data=result_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档详情失败: {str(e)}"
        )


@router.post(
    "/documents/{document_id}/preview-chunks",
    summary="preview_document_chunks          按 chunk_size 与 chunk_overlap 预览文档切分结果。",
    operation_id="previewDocumentChunks",
    responses={400: {"description": "文件类型不支持"}, 404: {"description": "文档或文件不存在"}, 500: {"description": "文档解析失败"}},
)
async def preview_document_chunks(
        document_id: int,
        session: DBSession,
        user: CurrentUser,
        chunk_size: int = 500,
        chunk_overlap: int = 50
):
    print(f"===== preview_document_chunks 被调用 =====")
    print(f"document_id: {document_id}")
    print(f"chunk_size: {chunk_size}, chunk_overlap: {chunk_overlap}")
    """
    预览文档切分结果（调用ETL管道服务）
    """
    try:
        stmt = select(Document).where(Document.doc_id == document_id, Document.is_deleted.is_(False))
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )

        file_path = _resolve_document_file_path(document.file_path)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档文件不存在或路径无效"
            )

        document_text = ""
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                document_text = f.read()
        elif file_ext in ['.docx', '.doc']:
            document_text = extract_text_from_docx(file_path)
        elif file_ext == '.pdf':
            document_text = extract_text_from_pdf(file_path)
        elif file_ext == '.csv':
            document_text = extract_text_from_csv(file_path)
        elif file_ext == '.md':
            document_text = extract_text_from_markdown(file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_ext}"
            )

        document_text = clean_text(document_text)

        splitter = DocumentTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        chunk_texts = splitter.split_text(document_text)

        chunks_result = []
        for i, chunk in enumerate(chunk_texts):
            chunks_result.append({
                "chunk_index": i,
                "content": chunk,
                "length": len(chunk),
                "start_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
            })

        return BaseResponse(data={
            "document_id": document_id,
            "document_name": document.doc_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "total_chunks": len(chunk_texts),
            "chunks": chunks_result,
            "stats": splitter.stats
        })

    except HTTPException:
        raise
    except Exception as e:
        print(f"预览文档切分失败: {str(e)}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档解析失败: {str(e)}"
        )

class ChunkItem(BaseModel):
    chunk_index: Optional[int] = None
    content: str

class GenerateVectorsRequest(BaseModel):
    chunks: Union[List[str], List[ChunkItem]]
    target_index: str = "default_vector_index"

@router.post(
    "/documents/{document_id}/generate-vectors",
    summary="generate_document_vectors          根据已切分文本块生成向量并返回结果。",
    operation_id="generateDocumentVectors",
    responses={400: {"description": "请求参数不合法"}, 404: {"description": "文档不存在"}, 500: {"description": "向量生成失败"}},
)
async def generate_document_vectors(
        document_id: int,
        session: DBSession,
        user: CurrentUser,
        request: GenerateVectorsRequest
):
    """
    为文档切分块生成向量（配合前端调用）

    参数:
        document_id: 文档ID
        chunks: 切分后的文本块列表（支持字符串数组或对象数组）
        target_index: 目标向量索引名称
    """
    try:
        stmt = select(Document).where(Document.doc_id == document_id, Document.is_deleted.is_(False))
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            return BaseResponse(
                code=status.HTTP_404_NOT_FOUND,
                msg="文档不存在",
                data=None
            )

        valid_chunks = []
        for chunk in request.chunks:
            content = chunk.content.strip()
            if content:
                valid_chunks.append(content)

        if not valid_chunks:
            return BaseResponse(
                code=status.HTTP_400_BAD_REQUEST,
                msg="没有有效的文本块需要处理",
                data=None
            )

        result = await generate_document_embeddings(valid_chunks)

        if result["status"] == "error":
            return BaseResponse(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                msg=f"向量生成失败: {result.get('error', '未知错误')}",
                data=None
            )

        result_data = {
            "doc_id": document.doc_id,
            "doc_name": document.doc_name,
            "chunks_count": len(valid_chunks),
            "vectors_count": result["embeddings_count"],
            "vector_dimension": result["embedding_dim"],
            "target_index": request.target_index,
            "vectors": result["embeddings"]
        }

        return BaseResponse(data=result_data)

    except asyncio.TimeoutError:
        return BaseResponse(
            code=status.HTTP_504_GATEWAY_TIMEOUT,
            msg="向量生成任务超时",
            data=None
        )
    except Exception as e:
        return BaseResponse(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=f"生成文档向量失败: {str(e)}",
            data=None
        )


@router.post(
    "/documents/{document_id}/approve",
    summary="approve_and_parse_document          审核通过文档并将切分块向量写入向量库。",
    operation_id="approveAndParseDocument",
    responses={400: {"description": "文档状态或参数不合法"}, 404: {"description": "文档不存在"}, 500: {"description": "审核并解析失败"}},
)
async def approve_and_parse_document(
        document_id: int,
        session: DBSession,
        user: CurrentUser,
        request: GenerateVectorsRequest
):
    """审核并解析文档，进行向量入库"""
    try:
        stmt = select(Document).where(Document.doc_id == document_id, Document.is_deleted.is_(False))
        result = await session.execute(stmt)
        document = result.scalar_one_or_none()
        if not document:
            return BaseResponse(code=status.HTTP_404_NOT_FOUND, msg="文档不存在")

        if document.status == "approved":
            return BaseResponse(code=status.HTTP_400_BAD_REQUEST, msg="文档已审核通过")

        kb_id = document.kb_id

        uploader_type = document.uploader_type
        if not uploader_type:
            return BaseResponse(code=status.HTTP_400_BAD_REQUEST, msg="文档没有上传者类型")

        uploader_id = document.uploader_id
        if not uploader_id:
            return BaseResponse(code=status.HTTP_400_BAD_REQUEST, msg="文档没有上传者id")

        valid_chunks = []
        for chunk in request.chunks:
            content = chunk.content.strip()
            if content:
                valid_chunks.append(content)

        if not valid_chunks:
            return BaseResponse(code=status.HTTP_400_BAD_REQUEST, msg="文档解析失败")

        settings = get_settings()
        runtime_cfg = await get_system_config_map(session, keys=["embedding_model_path", "embedding_device"])
        embedding_model_path = str(
            resolve_local_embedding_model_path(
                model_path=runtime_cfg.get("embedding_model_path") or settings.bge_model_path,
                models_root=settings.embedding_models_root,
                model_name=settings.bge_model_name,
            )
        )
        embedding_device = resolve_embedding_device(runtime_cfg.get("embedding_device") or settings.embedding_device)

        result = await generate_document_embeddings(
            valid_chunks,
            model_path=embedding_model_path,
            device=embedding_device,
        )

        if result["status"] == "error":
            return BaseResponse(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                msg=f"向量生成失败: {result.get('error', '未知错误')}",
                data=None
            )

        vector_store = get_vector_store(
            collection_name="default",
            persist_directory=settings.chroma_path,
            embedding_device=embedding_device,
            model_path=embedding_model_path,
        )

        deleted_count = vector_store.delete_document_chunks(
            document_id=document.doc_id,
            uploader_type=uploader_type,
            uploader_id=uploader_id
        )
        print(f"删除了 {deleted_count} 个已有的文本块")

        inserted_count = vector_store.add_document_chunks_to_knowledge_base(
            chunks=valid_chunks,
            document_id=document.doc_id,
            uploader_type=uploader_type,
            uploader_id=uploader_id,
            document_name=document.doc_name,
            source_type=document.doc_type,
            source_location=document.file_path,
            precomputed_embeddings=result["embeddings"]
        )

        document.status = "approved"
        document.chunk_count = len(valid_chunks)
        await session.commit()

        return BaseResponse(data={
            "doc_id": document.doc_id,
            "doc_name": document.doc_name,
            "kb_id": kb_id,
            "uploader_type": uploader_type,
            "uploader_id": uploader_id,
            "chunks_count": len(valid_chunks),
            "vectors_count": result["embeddings_count"],
            "vector_dimension": result["embedding_dim"],
            "target_index": request.target_index,
            "vectors_inserted": inserted_count,
            "vector_collection": f"{uploader_type}_{uploader_id}",
            "status": "approved"
        })

    except Exception as e:
        await session.rollback()
        return BaseResponse(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=f"审核并解析失败: {str(e)}"
        )


@router.post(
    "/documents/{document_id}/reject",
    summary="reject_document_api          将文档状态更新为 rejected。",
    operation_id="rejectDocument",
    responses={404: {"description": "文档不存在或状态不允许驳回"}, 500: {"description": "驳回文档失败"}},
)
async def reject_document_api(
        document_id: int,
        session: DBSession,
        user: CurrentUser
):
    """驳回文档，将文档状态改为rejected"""
    try:
        document = await reject_document(session, document_id)

        if not document:
            return BaseResponse(code=status.HTTP_404_NOT_FOUND, msg="文档不存在或状态不允许驳回")
        return BaseResponse(data={
            "doc_id": document.doc_id,
            "doc_name": document.doc_name,
            "status": "rejected"
        })
    except Exception as e:
        await session.rollback()
        return BaseResponse(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=f"驳回文档失败: {str(e)}"
        )


@router.get(
    "/documents/{document_id}/preview",
    summary="preview_document          读取原始文档文件并按文件类型返回二进制流。",
    operation_id="previewDocumentFile",
    responses={404: {"description": "文档或文件不存在"}, 500: {"description": "预览文档失败"}},
)
async def preview_document(
        document_id: int,
        session: DBSession,
        user: CurrentUser
):
    """
    预览文档文件（下载原始文件内容）
    """
    try:
        document = await get_document_by_id(session, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        if not document.file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档文件路径不存在"
            )
        file_path = _resolve_document_file_path(document.file_path)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档文件不存在"
            )
        file_bytes = read_file_bytes(file_path)

        file_ext = os.path.splitext(file_path)[1].lower()
        content_type_map = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.md': 'text/markdown'
        }
        content_type = content_type_map.get(file_ext, 'application/octet-stream')
        filename = document.doc_name or f"document{document_id}{file_ext}"

        response=Response(
            content=file_bytes,
            media_type=content_type,
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览文档失败: {str(e)}"
        )


@router.post(
    "/documents/{document_id}/intelligent-preview",
    summary="preview_intelligent_chunks          执行抽取、清洗、切分流程并返回智能切分结果。",
    operation_id="previewIntelligentChunks",
    responses={400: {"description": "文档抽取或清洗失败"}, 404: {"description": "文档或文件不存在"}, 500: {"description": "智能切分失败"}},
)
async def preview_intelligent_chunks(
        document_id: int,
        session: DBSession,
        user: CurrentUser,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        splitter_type: str = "semantic",
        similarity_threshold: float = 0.7,
        model_name: str = "data/bge-model/BAAI/bge-base-zh-v1.5"
):
    """
    智能文档切分预览（支持语义和递归两种切分策略）
    完整数据处理流程：抽取 -> 清洗 -> 拆分
    """
    from pathlib import Path
    from pydantic import BaseModel
    import asyncio
    import os
    import yaml
    from arq import create_pool
    from fastapi import APIRouter, HTTPException, status, Query
    from typing import Optional, Union, List
    """
    智能文档切分预览（支持语义和递归两种切分策略）
    完整数据处理流程：抽取 -> 清洗 -> 拆分
    """
    try:
        document = await get_document_by_id(session, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )

        file_path = document.file_path
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档文件路径不存在"
            )

        absolute_path = _resolve_document_file_path(file_path)
        if not absolute_path or not os.path.exists(absolute_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档文件不存在或路径无效"
            )

        print(f"开始读取配置文件")
        sources_config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'data_pipeline',
                                           'sources.yaml')

        if not os.path.exists(sources_config_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="配置文件不存在"
            )

        with open(sources_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        sources = config.get('sources', [])

        print(f"开始匹配文件类型配置")
        file_ext = os.path.splitext(absolute_path)[1].lower()
        matched_source = None

        for source in sources:
            if not source.get('enabled', True):
                continue

            source_type = source.get('type')

            if source_type == 'filesystem':
                file_patterns = source.get('file_patterns', [])
                for pattern in file_patterns:
                    if any(ext in pattern for ext in [file_ext, file_ext[1:]]):  
                        matched_source = source
                        break
            elif source_type == 'csv_excel':
                if file_ext in ['.csv', '.xls', '.xlsx']:
                    matched_source = source
                    break

            if matched_source:
                break

        if not matched_source:
            print("未匹配到配置，使用默认配置")
            matched_source = {
                'name': '默认配置',
                'type': 'filesystem' if file_ext in ['.pdf', '.docx', '.md', '.txt'] else 'csv_excel',
                'enabled': True,
                'cleaning_steps': [
                    {
                        "type": "regex",
                        "pattern": r'[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]',
                        "replace_with": "",
                        "column": "content"
                    },
                    {
                        "type": "regex",
                        "pattern": r'[ \t]+',
                        "replace_with": " ",
                        "column": "content"
                    },
                    {
                        "type": "dropna",
                        "subset": ["content"]
                    }
                ]
            }

        print(f"匹配到配置: {matched_source.get('name')}")

        print(f"开始抽取文档: {document.doc_name}")

        if matched_source.get('type') == 'filesystem':
            source_config = {
                'name': matched_source.get('name'),
                'type': 'filesystem',
                'enabled': True,
                'base_path': str(Path(absolute_path).parent),
                'file_patterns': [Path(absolute_path).name],
                'recursive': matched_source.get('recursive', False),
                'encoding': matched_source.get('encoding', 'utf-8')
            }
        else:
            source_config = {
                'name': matched_source.get('name'),
                'type': 'csv_excel',
                'enabled': True,
                'file_path': absolute_path,
                'encoding': matched_source.get('encoding', 'utf-8'),
                'separator': matched_source.get('separator', ','),
                'header': matched_source.get('header', 0),
                'sheet_name': matched_source.get('sheet_name', 0)
            }

        extractor = ExtractorFactory.create_extractor(source_config)
        if not extractor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法创建抽取器"
            )

        extracted_df = extractor.extract()
        if extracted_df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文档抽取失败，无法获取内容"
            )

        print(f"抽取完成，获取 {len(extracted_df)} 条记录")


        print("开始清洗数据")
        cleaning_pipeline = CleaningPipeline()

        cleaning_steps = matched_source.get('cleaning_steps', [])

        if not cleaning_steps:
            cleaning_steps = [
                {
                    "type": "regex",
                    "pattern": r'[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]',
                    "replace_with": "",
                    "column": "content"
                },
                {
                    "type": "regex",
                    "pattern": r'[ \t]+',
                    "replace_with": " ",
                    "column": "content"
                },
                {
                    "type": "dropna",
                    "subset": ["content"]
                }
            ]

        cleaning_pipeline.add_cleaner(matched_source.get('name'), cleaning_steps)
        cleaned_df = cleaning_pipeline.clean_source(matched_source.get('name'), extracted_df)

        if cleaned_df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="数据清洗后为空"
            )

        print(f"清洗完成，剩余 {len(cleaned_df)} 条记录")

        print("开始文本切分")

        all_content = "\n\n".join(cleaned_df['content'].tolist())
        splitter = TextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            splitter_type=splitter_type,
            model_name=model_name,
            similarity_threshold=similarity_threshold
        )

        chunks = splitter.split_text(all_content)

        chunks_result = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"doc_{document_id}_chunk_{i}"
            chunks_result.append({
                "chunk_id": chunk_id,
                "chunk_index": i,
                "content": chunk,
                "length": len(chunk),
                "start_preview": chunk[:100] + "..." if len(chunk) > 100 else chunk,
                "document_id": document_id,
                "source_type": document.doc_type or "document",
                "source_location": document.file_path or "",
            })

        print(f"切分完成，生成 {len(chunks)} 个文本块")

        return BaseResponse(data={
            "document_id": document_id,
            "document_name": document.doc_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "splitter_type": splitter_type,
            "similarity_threshold": similarity_threshold,
            "total_chunks": len(chunks),
            "chunks": chunks_result,
            "stats": splitter.stats,
            "extraction_count": len(extracted_df),
            "cleaning_count": len(cleaned_df)
        })

    except HTTPException:
        raise
    except Exception as e:
        print(f"智能切分预览失败: {str(e)}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"智能切分失败: {str(e)}"
        )
