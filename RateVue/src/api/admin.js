import request from '@/utils/request'

export const adminLogin1 = admin =>  request.post('/api/admin/login', admin)

export const getFiveStarMerchants = () => request.get('/api/admin/five-star-merchants')

export const getMostCommentedMerchants = () => request.get('/api/admin/most-commented-merchants')

export const getHighestRatedMerchants = () => request.get('/api/admin/highest-rated-merchants')

export const getRatingDistribution = () => request.get('/api/admin/rating-distribution')

export const getUserGrowthData = () => request.get('/api/admin/user-growth')

export const getCurrentAdmin = () => request.get('/api/admin/getInfo');
