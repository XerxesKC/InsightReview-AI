import request from '@/utils/request';
export const searchComment = (query) => request.get('/api/comment/selectByMerchantId', { params: query });
export const searchUserComment = (query) => request.get('/api/comment/getCommentsByUserId', { params: query });
export const searchPostComment = (query) => request.get('/api/comment/selectByMerchantIdAndPostId', { params: query });
export const getMerchantPostComments1 = merchantId => request.get('/api/comment/getMerchantPostComments', {params: {merchantId}})

export const getMerchantComments1 = merchantId => request.get('/api/comment/getMerchantComments', {params: {merchantId}})

export const getComments1 = () => request.get('/api/comment/getComments');

export const addComment = (comment) => request.post('/api/comment/add', comment)

export const deleteComment1 = (comment) => request.post('/api/comment/deleteComment',  comment );

export const changeCommentStatus1 = (comment) => request.post('/api/comment/changeCommentStatus',  comment );

export const deleteComment = (commentId) => request.post('/api/comment/userDelete', { commentId });
export const addReply = (reply) => {return request.post('/api/reply/add', reply)}

export const queryReplies = (commentId, replyTo) => {
    return request.get('/api/reply/queryByCommentAndUser', {
        params: { commentId, replyTo }
    })
}
