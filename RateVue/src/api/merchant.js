import request from '@/utils/request'
import merchant from "@/router/routes/merchant";
import {List} from "@element-plus/icons-vue";

export const merchantSearchService = (query) => request.post('/api/merchant/search', query);

export const merchantList = (params) => request.post('/api/merchant/list', { params });

export const getMerchantList = (params) => request.get('/api/merchant/getList', { params })

export const merchantLogin1 = merchant =>  request.post('/api/merchant/login', merchant)

export const merchantRegister1 = merchant =>  request.post('/api/merchant/insert', merchant)

export const getParentList1 = () =>  request.get('/api/category/getParentList')

export const getCurrentMerchant = () => request.get('/api/merchant/getInfo');

export const updateMerchant = merchant => request.post('/api/merchant/update', merchant);

export const selectById = id => request.get('/api/merchant/selectById', { params: { id } });

export const verifyMerchant = (data) => request({
    url: '/api/merchant/verify',
    method: 'post',
    params: {
        merchantId: data.merchantId,
        verificationStatus: data.status,
        review: data.review || ''
    },
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
})

export const toggleMerchantStatus = (data) => request.post('/api/merchant/status',
    new URLSearchParams({
        merchantId: data.merchantId,
        status: data.status
    }), {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    }
)

export const deleteMerchant = (merchantId) => request.post('/api/merchant/deleteById', null, {
    params: { merchantId }
})

export const uploadMerchantImage = (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/api/file/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

