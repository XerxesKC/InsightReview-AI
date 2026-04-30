import request from '@/utils/request';

export const createKnowledgeBase = (data) => request.post('/api/v1/knowledge_base/create', data);

export const getKnowledgeBases = (params = {}) => request.get('/api/v1/knowledge_base/list', { params });

export const updateKnowledgeBase = (id, data) => request.post(`/api/v1/knowledge_base/update?kb_id=${id}`, data);

export const deleteKnowledgeBase = (id) => request.post(`/api/v1/knowledge_base/delete?kb_id=${id}`);

export const getKnowledgeBaseOptions = () => request.get('/api/v1/knowledge_base/options');

export const getEmbeddingModels = () => request.get('/api/v1/knowledge_base/models');

export const getVectorCollections = (ownerType = null, ownerId = null) => {
  const params = {};
  if (ownerType) params.owner_type = ownerType;
  if (ownerId) params.owner_id = ownerId;
  return request.get('/api/v1/knowledge_base/vector_collections', { params });
};

export const getOwners = (ownerType, keyword = "") => request.get(`/api/v1/knowledge_base/owners?owner_type=${ownerType}&keyword=${keyword}`);
