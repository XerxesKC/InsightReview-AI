import MerchantLayout from '@/layouts/MerchantLayout.vue'

const MerchantProfile = () => import('@/views/merchant/MerchantProfile.vue')
const ContentManage = () => import('@/views/merchant/ContentManage.vue')
const CommentManage = () => import('@/views/merchant/CommentManage.vue')
const MerchantAnalytics = () => import('@/views/merchant/MerchantAnalytics.vue')
const DocumentManage = () => import('@/views/merchant/DocumentManage.vue')
const IntelligentAssistant = () => import('@/views/merchant/IntelligentAssistant.vue')



export default {
    path: '/merchant',
    component: MerchantLayout,
    meta: {
        requiresAuth: true,
        role: 'merchant',
        requiresMerchantAuth: true,
        breadcrumb: ['商家中心']
    },
    children: [
        {
            path: 'profile',
            name: 'merchantProfile',
            component: MerchantProfile,
            meta: {
                title: '店铺设置',
                breadcrumb: ['商家中心', '店铺管理']
            }
        },
        {
            path: 'contents',
            name: 'contentManage',
            component: ContentManage,
            meta: {
                title: '内容管理',
                breadcrumb: ['商家中心', '动态管理']
            }
        },
        {
            path: 'comments',
            name: 'merchantCommentManage',
            component: CommentManage,
            meta: {
                title: '评价管理',
                breadcrumb: ['商家中心', '评价处理']
            }
        },
        {
            path: 'documents',
            name: 'documentManage',
            component: DocumentManage,
            meta: {
                title: '文档管理',
                breadcrumb: ['商家中心', '文档管理']
            }
        },
        {
            path: 'analytics',
            name: 'merchantAnalytics',
            component: MerchantAnalytics,
            meta: {
                title: '数据分析',
                breadcrumb: ['商家中心', '经营数据']
            }
        },
        {
            path: 'merchantAssistant',
            name: 'merchantIntelligentAssistant',
            component: IntelligentAssistant,
            meta: {
                title: '智能助手',
                breadcrumb: ['商家中心', '智能助手']
            }
        },
        { path: '', redirect: { name: 'merchantProfile' } }
    ]
}
