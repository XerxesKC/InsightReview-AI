import sqlite3
from datetime import datetime
from pathlib import Path
from app.core.config import get_settings
from app.core.datetime_utils import to_rfc3339
from fastapi import APIRouter, File, HTTPException, UploadFile, status, Form, Response
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBSession
from app.db.crud import bind_documents_to_kb, create_document, get_system_config_value, list_documents,\
    soft_delete_document, update_document,\
    get_document_by_id, check_duplicate_document, deprecated_document, list_document_versions, activate_document
from app.rag.embeddings import resolve_local_embedding_model_path
from app.services.model_discovery import list_local_embedding_models
from app.services.file_handler import save_upload_file
from app.worker.tasks import enqueue_ingest_document

from app.db.crud import (
    create_knowledge_base as create_kb_db,
    list_knowledge_bases as list_kbs_db,
    list_owners,
    update_knowledge_base as update_kb_db,
    soft_delete_knowledge_base as delete_kb_db,
    get_knowledge_base as get_kb_db
)
from app.core.response import BaseResponse

router = APIRouter(tags=["knowledge"])


class KnowledgeBaseCreateReq(BaseModel):
    admin_id: str
    name: str
    description: str
    owner_type: str
    owner_id: str
    embedding_model: str
    chroma_collection: str

class KnowledgeBaseUpdateReq(BaseModel):
    name: str | None = None
    description: str | None = None
    owner_type: str | None = None
    owner_id: str | None = None
    embedding_model: str | None = None
    chroma_collection: str | None = None

@router.post(
    "/knowledge/upload",
    summary="upload_document          上传文档并创建待审核记录，同时投递入库任务。",
    operation_id="uploadKnowledgeDocument",
)
async def upload_document(
    session: DBSession,
    uploader_type: str = Form(...),
    uploader_id: int | None = Form(None),
    file: UploadFile = File(...),
    kb_id: int | None = Form(None),
    chunk_size: int | None = Form(None),
    chunk_overlap: int | None = Form(None),
):
    max_upload_size_mb: int | None = None
    max_size_str = await get_system_config_value(session, key="file_upload_max_size_mb")
    if max_size_str is not None:
        try:
            parsed = int(max_size_str)
            if parsed > 0:
                max_upload_size_mb = parsed
        except ValueError:
            max_upload_size_mb = None

    stored_path = await save_upload_file(file, max_upload_size_mb=max_upload_size_mb)
    suffix = Path(file.filename or stored_path.name).suffix.lower().lstrip(".") or "txt"
    file_size = stored_path.stat().st_size
    document = await create_document(
        session,
        doc_name=file.filename or stored_path.name,
        doc_type=suffix,
        doc_size=file_size,
        file_path=str(stored_path),
        uploader_type=uploader_type,
        uploader_id=uploader_id,
        kb_id=kb_id,
        status="pending",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    task_id = await enqueue_ingest_document(str(stored_path))
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "doc_id": document.doc_id,
            "task_id": task_id,
            "status": document.status,
            "file_path": str(stored_path),
            "uploader_type": document.uploader_type,
            "uploader_id": document.uploader_id,
        }
    }

@router.get(
    "/knowledge/list",
    summary="get_documents          按用户与知识库筛选文档列表。",
    operation_id="listKnowledgeDocuments",
)
async def get_documents(
        session: DBSession,
        user_type: str,
        user_id: int,
        kb_id: int | None = None
):
    documents = await list_documents(session, user_type, user_id, kb_id=kb_id)
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "items": [
                {
                    "doc_id": item.doc_id,
                "kb_id": item.kb_id,
                "doc_name": item.doc_name,
                "doc_type": item.doc_type,
                "doc_size": item.doc_size,
                "file_path": item.file_path,
                "status": item.status,
                "uploader_type": item.uploader_type,
                "uploader_id": item.uploader_id,
                "chunk_size": item.chunk_size,
                "chunk_overlap": item.chunk_overlap,
                "chunk_count": item.chunk_count,
                "created_at": to_rfc3339(item.created_at),
                }
                for item in documents
            ]
        }
    }


@router.delete(
    "/knowledge/delete",
    summary="delete_document          软删除当前文档并同步删除同名历史版本。",
    operation_id="deleteKnowledgeDocument",
)
async def delete_document(document_id: int, session: DBSession):
    document = await get_document_by_id(session, document_id)

    if document is None or document.is_deleted == "T":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在或者您没有权限删除它。",
        )

    historical_documents = await list_document_versions(
        session,
        doc_name=document.doc_name,
        uploader_type=document.uploader_type,
        uploader_id=document.uploader_id,
        current_doc_id=document_id
    )

    deleted_document = await soft_delete_document(session, document_id)

    deleted_historical_count = 0
    for historical_doc in historical_documents:
        try:
            await soft_delete_document(session, historical_doc.doc_id)
            deleted_historical_count += 1
        except Exception as e:
            print(f"删除历史文件失败 {historical_doc.doc_id}: {e}")

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "items": [
                {
                    "doc_id": deleted_document.doc_id,
                    "deleted": True,
                    "status": "deleted",
                    "doc_name": deleted_document.doc_name,
                    "historical_documents_deleted": deleted_historical_count,
                    "total_deleted": deleted_historical_count + 1
                }
            ]
        }
    }

@router.post(
    "/knowledge/edit",
    summary="edit_document          上传新文件覆盖指定文档并重新进入待审核流程。",
    operation_id="editKnowledgeDocument",
)
async def edit_document(
        session: DBSession,
        file: UploadFile = File(...),
        doc_id: int = Form(...),
        kb_id: int | None = Form(None),
        chunk_size: int | None = Form(None),
        chunk_overlap: int | None = Form(None),
):
    max_upload_size_mb: int | None = None
    max_size_str = await get_system_config_value(session, key="file_upload_max_size_mb")
    if max_size_str is not None:
        try:
            parsed = int(max_size_str)
            if parsed > 0:
                max_upload_size_mb = parsed
        except ValueError:
            pass

    stored_path = await save_upload_file(file, max_upload_size_mb=max_upload_size_mb)
    file_size = stored_path.stat().st_size
    suffix = Path(file.filename or stored_path.name).suffix.lower().lstrip(".") or "txt"

    document = await update_document(
        session=session,
        doc_id=doc_id,
        doc_name=file.filename or stored_path.name,
        doc_type=suffix,
        doc_size=file_size,
        file_path=str(stored_path),
        status="pending",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        kb_id=kb_id,
    )
    task_id = await enqueue_ingest_document(str(stored_path))

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "doc_id": document.doc_id,
            "doc_name": document.doc_name,
            "status": document.status,
            "updated": True,
            "task_id": task_id
        }
    }

@router.get(
    "/knowledge/download",
    summary="download_document          按文档 ID 下载原始文件内容。",
    operation_id="downloadKnowledgeDocument",
)
async def download_document(
        doc_id: int,
        session: DBSession
):
    document = await get_document_by_id(session, doc_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该文件记录不存在或已被删除"
        )

    file_path = document.file_path

    if not file_path or not Path(file_path).is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="服务器上的实体文件已丢失"
        )

    return FileResponse(
        path=file_path,
        filename=document.doc_name,
        content_disposition_type="inline"
    )


@router.post(
    "/knowledge_base/create",
    response_model=BaseResponse[dict],
    summary="create_knowledge_base          创建知识库并尝试绑定向量库中已有文档。",
    operation_id="createKnowledgeBase",
)
async def create_knowledge_base(req: KnowledgeBaseCreateReq, db: DBSession):
    kb = await create_kb_db(
        db,
        admin_id=req.admin_id,
        name=req.name,
        description=req.description,
        owner_type=req.owner_type,
        owner_id=req.owner_id,
        embedding_model=req.embedding_model,
        chroma_collection=req.chroma_collection,
    )

    try:
        if req.chroma_collection:
            current_dir = Path(__file__).parent.parent.parent.parent
            db_path = current_dir / "data" / "chroma" / "chroma.sqlite3"
            
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM collections WHERE name = ?", (req.chroma_collection,))
                col_result = cursor.fetchone()
                
                if col_result:
                    col_id = col_result[0]
                    cursor.execute("SELECT id FROM segments WHERE collection = ?", (col_id,))
                    segments = cursor.fetchall()
                    segment_ids = [s[0] for s in segments]
                    
                    if segment_ids:
                        placeholders = ','.join(['?'] * len(segment_ids))
                        cursor.execute(f"""
                            SELECT DISTINCT em.string_value
                            FROM embedding_metadata em
                            JOIN embeddings e ON em.id = e.id
                            WHERE e.segment_id IN ({placeholders}) AND em.key = 'document_id'
                        """, segment_ids)
                        
                        docs = cursor.fetchall()
                        doc_ids = []
                        for d in docs:
                            if d[0] and str(d[0]).isdigit():
                                doc_ids.append(int(d[0]))
                        
                        if doc_ids:
                            updated_count = await bind_documents_to_kb(db, doc_ids, kb.kb_id)
                            print(f"✅ 成功将 {updated_count} 个文档绑定到了知识库 ID: {kb.kb_id}")
                
                conn.close()
    except Exception as e:
        print(f"❌ 提取 Collection 文档 ID 并更新 document 表失败: {e}")

    return BaseResponse(code=200, msg="知识库创建成功", data={
        "id": kb.kb_id,
        "admin_id": kb.admin_id,
        "name": kb.name,
        "description": kb.description,
        "owner_type": kb.owner_type,
        "owner_id": kb.owner_id,
        "embedding_model": kb.embedding_model,
        "chroma_collection": kb.chroma_collection,
        "status": "active",
    })
async def get_owner_name(db: DBSession, owner_type: str, owner_id: str) -> str:
    """
    根据 owner_type 和 owner_id 从对应的表中获取负责人名字

    Args:
        db: 数据库会话
        owner_type: 所有者类型 (merchant, admin)
        owner_id: 所有者ID

    Returns:
        负责人名字
    """
    from sqlalchemy import text

    try:
        if owner_type == "merchant":
            query = text("SELECT merchant_name FROM merchant WHERE merchant_id = :owner_id AND (is_deleted = 'F' OR is_deleted IS NULL)")
            result = await db.execute(query, {"owner_id": owner_id})
            row = result.fetchone()
            return row[0] if row else f"未知商家({owner_id})"
        elif owner_type == "admin":
            query = text("SELECT admin_name FROM admin WHERE admin_id = :owner_id AND (is_deleted = 'F' OR is_deleted IS NULL)")
            result = await db.execute(query, {"owner_id": owner_id})
            row = result.fetchone()
            return row[0] if row else f"未知管理员({owner_id})"
        else:
            return f"未知类型({owner_id})"
    except Exception as e:
        print(f"Error getting owner name: {e}")
        return f"未知({owner_id})"

@router.get(
    "/knowledge_base/list",
    response_model=BaseResponse[list],
    summary="list_knowledge_bases          按名称、负责人和创建时间范围筛选知识库。",
    operation_id="listKnowledgeBases",
)
async def list_knowledge_bases(
    db: DBSession,
    name: str | None = None,
    owner_type: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None
):
    created_from_dt = None
    if created_from:
        try:
            if ' ' in created_from:
                created_from_dt = datetime.strptime(created_from, '%Y-%m-%d %H:%M:%S')
            else:
                created_from_dt = datetime.fromisoformat(created_from)
        except Exception as e:
            print(f"Invalid created_from format: {e}")
    
    created_to_dt = None
    if created_to:
        try:
            if ' ' in created_to:
                created_to_dt = datetime.strptime(created_to, '%Y-%m-%d %H:%M:%S')
            else:
                created_to_dt = datetime.fromisoformat(created_to)
        except Exception as e:
            print(f"Invalid created_to format: {e}")
    
    kbs = await list_kbs_db(
        db,
        name=name,
        owner_type=owner_type,
        created_from=created_from_dt,
        created_to=created_to_dt
    )
    
    knowledge_bases_with_owner = []
    for kb in kbs:
        owner_name = await get_owner_name(db, kb.owner_type, str(kb.owner_id))
        
        knowledge_base_data = {
            "id": kb.kb_id,
            "admin_id": kb.admin_id,
            "name": kb.name,
            "description": kb.description,
            "owner_type": kb.owner_type,
            "owner_id": kb.owner_id,
            "owner_name": owner_name,  
            "embedding_model": kb.embedding_model,
            "chroma_collection": kb.chroma_collection,
            "created_at": to_rfc3339(kb.created_at),  
            "status": "active",
        }
        knowledge_bases_with_owner.append(knowledge_base_data)
    
    return BaseResponse(code=200, msg="知识库列表", data=knowledge_bases_with_owner)

@router.get(
    "/knowledge_base/options",
    response_model=BaseResponse[dict],
    summary="get_kb_options          返回可选向量模型、默认模型和向量集合列表。",
    operation_id="getKnowledgeBaseOptions",
)
def get_kb_options():
    import chromadb

    settings = get_settings()
    chroma_dir = Path(settings.chroma_path)
    model_infos = list_local_embedding_models(settings.embedding_models_root)
    model_names = [item["name"] for item in model_infos]

    default_model_name = ""
    try:
        default_model_path = resolve_local_embedding_model_path(
            model_path=settings.bge_model_path,
            models_root=settings.embedding_models_root,
            model_name=settings.bge_model_name,
        )
        default_model_name = next(
            (item["name"] for item in model_infos if Path(item["path"]) == default_model_path),
            settings.bge_model_name,
        )
    except Exception:
        default_model_name = settings.bge_model_name

    collections = []
    if chroma_dir.exists():
        try:
            client = chromadb.PersistentClient(path=str(chroma_dir))
            collections = [col.name for col in client.list_collections()]
        except Exception as e:
            print(f"Error listing collections: {e}")

    return BaseResponse(code=200, msg="知识库选项", data={
        "embedding_models": model_names,
        "embedding_model_details": model_infos,
        "default_embedding_model": default_model_name,
        "vector_collections": collections,
    })

@router.get(
    "/knowledge_base/vector_collections",
    response_model=BaseResponse[list],
    summary="get_vector_collections          返回本地向量库集合，可按负责人优先排序。",
    operation_id="getKnowledgeVectorCollections",
)
def get_vector_collections(owner_type: str | None = None, owner_id: str | None = None):
    import chromadb
    from pathlib import Path
    
    current_dir = Path(__file__).parent.parent.parent.parent
    chroma_dir = current_dir / "data" / "chroma"
    
    if not chroma_dir.exists():
        return BaseResponse(code=200, msg="向量库目录不存在", data=[])

    try:
        client = chromadb.PersistentClient(path=str(chroma_dir))
        collections = [col.name for col in client.list_collections()]
        
        if owner_type and owner_id:
            target_collection = f"{owner_type}_{owner_id}"
            if target_collection in collections:
                collections.remove(target_collection)
                collections.insert(0, target_collection)
    except Exception as e:
        print(f"Error listing collections: {e}")
        return BaseResponse(code=200, msg="获取向量库列表失败", data=[])
    
    return BaseResponse(code=200, msg="可选向量库列表", data=collections)

@router.get(
    "/knowledge_base/models",
    response_model=BaseResponse[list],
    summary="get_embedding_models          返回当前可用的 Embedding 模型名称列表。",
    operation_id="getKnowledgeEmbeddingModels",
)
def get_embedding_models():
    settings = get_settings()
    model_infos = list_local_embedding_models(settings.embedding_models_root)
    models = [item["name"] for item in model_infos]

    return BaseResponse(code=200, msg="可选模型列表", data=models)

@router.get(
    "/knowledge_base/owners",
    response_model=BaseResponse[list],
    summary="get_owners          按负责人类型与关键字检索负责人选项。",
    operation_id="getKnowledgeOwners",
)
async def get_owners(db: DBSession, owner_type: str, keyword: str = ""):
    """
    获取指定部门的负责人列表

    Args:
        db: 数据库会话
        owner_type: 部门类型 (user, merchant, admin)
        keyword: 搜索关键字
    """
    try:
        owners = await list_owners(db, owner_type, keyword)
        return BaseResponse(code=200, msg="负责人列表", data=owners)
    except Exception as e:
        return BaseResponse(code=500, msg=f"获取负责人列表失败: {str(e)}", data=[])

@router.get(
    "/knowledge_base/{kb_id}",
    response_model=BaseResponse[dict],
    summary="get_knowledge_base          按知识库 ID 返回完整详情。",
    operation_id="getKnowledgeBaseById",
)
async def get_knowledge_base(kb_id: int, db: DBSession):
    kb = await get_kb_db(db, kb_id=kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return BaseResponse(code=200, msg="获取知识库成功", data={
        "id": kb.kb_id,
        "admin_id": kb.admin_id,
        "name": kb.name,
        "description": kb.description,
        "owner_type": kb.owner_type,
        "owner_id": kb.owner_id,
        "embedding_model": kb.embedding_model,
        "chroma_collection": kb.chroma_collection,
        "status": "active",
    })

@router.post(
    "/knowledge_base/update",
    response_model=BaseResponse[dict],
    summary="update_knowledge_base          更新知识库的名称、描述、负责人和向量配置。",
    operation_id="updateKnowledgeBase",
)
async def update_knowledge_base(db: DBSession, kb_id: int, req: KnowledgeBaseUpdateReq):
    kb = await update_kb_db(
        db,
        kb_id=kb_id,
        name=req.name,
        description=req.description,
        owner_type=req.owner_type,
        owner_id=req.owner_id,
        embedding_model=req.embedding_model,
        chroma_collection=req.chroma_collection,
    )
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return BaseResponse(code=200, msg="知识库更新成功", data={
        "id": kb.kb_id,
        "admin_id": kb.admin_id,
        "name": kb.name,
        "description": kb.description,
        "owner_type": kb.owner_type,
        "owner_id": kb.owner_id,
        "embedding_model": kb.embedding_model,
        "chroma_collection": kb.chroma_collection,
        "status": "active",
    })

@router.post(
    "/knowledge_base/delete",
    response_model=BaseResponse[dict],
    summary="delete_knowledge_base          软删除指定知识库。",
    operation_id="deleteKnowledgeBase",
)
async def delete_knowledge_base(db: DBSession, kb_id: int):
    kb = await delete_kb_db(db, kb_id=kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return BaseResponse(code=200, msg="知识库删除成功", data={
        "id": kb.kb_id,
        "deleted": True,
    })


@router.get(
    "/knowledge/check-duplicate",
    summary="check_duplicate_document_api          检查指定上传者下是否存在同名文档。",
    operation_id="checkDuplicateKnowledgeDocument",
)
async def check_duplicate_document_api(
        session: DBSession,
        doc_name: str,
        uploader_type: str,
        uploader_id: int
):
    """检查是否有同名文档"""
    duplicate_documents = await check_duplicate_document(
        session,
        doc_name=doc_name,
        uploader_type=uploader_type,
        uploader_id=uploader_id
    )

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "exists": len(duplicate_documents) > 0,
            "duplicate_count": len(duplicate_documents),
            "duplicate_documents": [
                {
                    "doc_id": doc.doc_id,
                }
                for doc in duplicate_documents
            ]
        }
    }


@router.post(
    "/knowledge/deprecated_document",
    summary="deprecated_document_api          将文档状态更新为 deprecated。",
    operation_id="deprecateKnowledgeDocument",
)
async def deprecated_document_api(document_id: int, session: DBSession):
    """将文档状态改为弃用"""
    deprecated_doc = await deprecated_document(session, document_id)
    if not deprecated_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "doc_id": deprecated_doc.doc_id,
            "status": deprecated_doc.status
        }
    }

@router.get(
    "/knowledge/history_document",
    summary="get_document_history          按文档名与上传者查询历史版本列表。",
    operation_id="getKnowledgeDocumentHistory",
)
async def get_document_history(
    session: DBSession,
    doc_name: str,
    uploader_type: str,
    uploader_id: int,
    current_doc_id: int
):
    """获取文档历史版本"""
    historical_documents = await list_document_versions(
        session,
        doc_name=doc_name,
        uploader_type=uploader_type,
        uploader_id=uploader_id,
        current_doc_id=current_doc_id
    )
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "items": [
                {
                    "doc_id": doc.doc_id,
                    "doc_name": doc.doc_name,
                    "doc_type": doc.doc_type,
                    "doc_size": doc.doc_size,
                    "status": doc.status,
                    "created_at": to_rfc3339(doc.created_at),
                    "file_path": doc.file_path
                }
                for doc in historical_documents
            ]
        }
    }

@router.post(
    "/knowledge/activate_document",
    summary="activate_document_api          将文档状态恢复为可用状态。",
    operation_id="activateKnowledgeDocument",
)
async def activate_document_api(document_id: int, session: DBSession):
    """激活文档"""
    activated_doc = await activate_document(session, document_id)
    if not activated_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "doc_id": activated_doc.doc_id,
            "status": activated_doc.status
        }
    }
