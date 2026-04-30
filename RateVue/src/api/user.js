import request from '@/utils/request';

export const userInfoService = (id) => request.get(`/api/user/getById/${id}`);

export const userSearch = (searchParams) => request.get('/api/user/search', { params: searchParams });

export const userLogin1 = user =>  request.post('/api/user/login', user);

export const userRegister = userData => request.post('/api/user/register', userData);

export const getCurrentUser = () => request.get('/api/user/getInfo');

export const updateCurrentUser = (userData) => request.post('/api/user/updateCurrentUser', userData);

export const getUserList = (params) => request.get('/api/user/list', { params });

export const updateUser = (userData) => request.post('/api/user/update', userData);

export const updateUserStatus = (userId, status) => request.post('/api/user/updateStatus', { userId, status });

export const deleteUser = (userId) => request.post(`/api/user/deleteById`, null, {
    params: { userId }
});

export const getUserLoginRecords = (userId, params) => request.get(`/api/user/${userId}/loginRecords`, { params });

export const getUserPaymentRecords = (userId, params) => request.get(`/api/user/${userId}/paymentRecords`, { params });

export const getUserFavoriteRecords = (userId, params) => request.get(`/api/user/${userId}/favoriteRecords`, { params });

export const getUserCollect = (userId, params = {}) => {
    return request({
        url: '/api/favorite/search',
        method: 'get',
        params: {
            userId,
            pageNum: params.pageNum || 1,
            pageSize: params.pageSize || 10,
            ...params
        }
    })
}

export const getFavoriteByUserAndMerchant = (userId, merchantId) => {
  return request({
    url: '/api/favorite/search',
    method: 'get',
    params: {
      userId,
      merchantId,
      pageNum: 1,
      pageSize: 1
    }
  })
}

export const addFavorite = (data) => {
  return request({
    url: '/api/favorite/insert',
    method: 'post',
    data
  })
}

export const deleteFavorite = (favoriteId) => {
    return request({
        url: '/api/favorite/delete',
        method: 'post',
        params: { favoriteId }
    })
}

export const updateFavorite = (favoriteId, tag) => {
    return request({
        url: '/api/favorite/update',
        method: 'post',
        data: {
            favoriteId,
            tag
        }
    })
}

export const getUsers1 = () => request.get('/api/user/getUsers', )
