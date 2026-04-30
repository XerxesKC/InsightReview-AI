
import request from '@/utils/request'


export const previewIntelligentChunks = (documentId, params) => {
  return request.post(`/api/v1/admin/documents/${documentId}/intelligent-preview`, null, { params })
}


export const generateVectors = (documentId, data) => {
  return request.post(`/api/v1/admin/documents/${documentId}/generate-vectors`, data)
}


export const analyzePandasData = (datasetReference, analysisQuery, userInstruction = null) => {
  return request.post('/api/v1/analysis/pandas-analyze', {
    dataset_reference: datasetReference,
    analysis_query: analysisQuery,
    user_instruction: userInstruction
  })
}


export const getAnalysisTemplates = () => {
  return request.get('/api/v1/analysis/pandas-analyze/templates')
}
