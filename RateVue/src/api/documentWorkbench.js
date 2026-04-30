import request from '@/utils/request';

export const getPendingDocuments = (params = {}) => {
  return request.get('/api/v1/admin/documents/pending', { params });
}

export const searchDocuments = (params = {}) => request.get('/api/v1/admin/doc-workbench/search', { params });

export const getDocumentDetail = (id) => request.get(`/api/v1/admin/documents/${id}`);

export const approveDocument = (id, data) => request.post(`/api/v1/admin/documents/${id}/approve`, data);
export const parseDocument = (id, data) => request.post(`/api/v1/admin/documents/${id}/parse`, data);
export const generateVectors = (id, data) => request.post(`/api/v1/admin/documents/${id}/generate-vectors`, data);
export const optimizeVectors = (id, data) => request.post(`/api/v1/admin/documents/${id}/optimize-vectors`, data);
export const rejectDocument = (id) => request.post(`/api/v1/admin/documents/${id}/reject`);
export const previewChunks = (id, params) => request.post(`/api/v1/admin/documents/${id}/preview-chunks`,null, { params });
export const previewDocument = (documentId) => {
  return request.get(`/api/v1/admin/documents/${documentId}/preview`, {
    responseType: 'blob'
  })
}
