import request from '@/utils/request'

export const merchantInsert= content => request.post('/api/merchantpost/postInsert', content)

export const getContents1 = merchantId => request.get('/api/merchantpost/getContents', {params: {merchantId}})

export const removeContentById= merchantPost => request.post('/api/merchantpost/deleteContent', merchantPost)

export const addLikeCount= merchantPost => request.post('/api/merchantpost/addLikeCount', merchantPost)
