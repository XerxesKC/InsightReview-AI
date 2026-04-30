import request from '@/utils/request'

export const getDialogueLogs = (params) => {
  return request({
    url: '/api/v1/dialogue-log/list',
    method: 'get',
    params
  })
}

export const getDialogueSessionDetail = (sessionId) => {
  return request({
    url: `/api/v1/dialogue-log/detail/${sessionId}`,
    method: 'get'
  })
}

export const exportDialogueLogs = (params) => {
  return request({
    url: '/api/v1/dialogue-log/export',
    method: 'get',
    params,
    responseType: 'blob'
  })
}

export const getDialogueAnalysis = (params) => {
  return request({
    url: '/api/v1/dialogue-log/analysis',
    method: 'get',
    params
  })
}
