import request from '@/utils/request';
export const categorySearchService = (categoryName) =>
    request.get('/api/category/getIdByName', {
        params: { categoryName }
    });

export const getCurrentCategoryName = (categoryId) => request.get('/api/category/getMerchantCategoryName', {params: {categoryId}})
