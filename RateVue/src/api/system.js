import request from '@/utils/request'

export const getEmbeddingModels = () =>
    request.get('/api/v1/admin/system/embedding-models')

export const setActiveEmbeddingModel = (payload) =>
    request.put('/api/v1/admin/system/embedding-model', payload)

export const getSystemParams = () => request.get('/api/v1/admin/system/params')

export const updateSystemParams = params =>
    request.put('/api/v1/admin/system/params', params)
