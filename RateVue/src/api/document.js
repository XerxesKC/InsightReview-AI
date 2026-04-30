import request from '@/utils/request'

export const uploadDocument = (formData, onUploadProgress) => {
    return request.post('/api/v1/knowledge/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        },
        onUploadProgress
    })
}

export const getDocumentList = (query) => {
    return request.get('/api/v1/knowledge/list', { params: query })
}

export const deleteDocument = (documentId) => {
    return request.delete('/api/v1/knowledge/delete', {
        params: { document_id: documentId }
    })
}

export const updateDocument = (formData, onUpdateProgress) => {
    return request.post('/api/v1/knowledge/edit', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        },
        onUpdateProgress
    })
}

export const downloadDocument = (documentId) => {
    return request.get('/api/v1/knowledge/download', {
        params: { doc_id: documentId },
        responseType: 'blob'
    })
}

export const checkDuplicateDocument = (params) => {
    return request.get('/api/v1/knowledge/check-duplicate', {
        params: params
    })
}
export const deprecatedDocument = (documentId) => {
    return request.post('/api/v1/knowledge/deprecated_document', null, {
        params: { document_id: documentId }
    })
}

export const getDocumentHistory = (params) => {
    return request.get('/api/v1/knowledge/history_document', {
        params: params
    })
}

export const activateDocument = (documentId) => {
    return request.post('/api/v1/knowledge/activate_document', null, {
        params: { document_id: documentId }
    })
}