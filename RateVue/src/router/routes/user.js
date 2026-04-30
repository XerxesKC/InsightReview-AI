import UserLayout from '@/layouts/UserLayout.vue'

const UserProfile = () => import('@/views/user/UserProfile.vue')
const ListSearch = () => import('@/views/user/search/ListSearch.vue')
const MapSearch = () => import('@/views/user/search/MapSearch.vue')
const ShopDetail = () => import('@/views/user/ShopDetail.vue')
const CollectionManage = () => import('@/views/user/CollectionManage.vue')
const UserComments = () => import('@/views/user/UserComments.vue')
const IntelligentAssistant = () => import('@/views/user/IntelligentAssistant.vue')

export default {
    path: '/user',
    component: UserLayout,
    meta: {
        requiresAuth: true,
        role: 'user',
        breadcrumb: ['用户中心']
    },
    children: [
        {
            path: 'profile',
            name: 'userProfile',
            component: UserProfile,
            meta: {
                title: '个人资料',
                breadcrumb: ['用户中心', '个人资料']
            }
        },
        {
            path: 'search/list',
            name: 'listSearch',
            component: ListSearch,
            meta: {
                title: '商家列表',
                keepAlive: true,
                breadcrumb: ['用户中心', '商家搜索']
            }
        },
        {
            path: 'search/map',
            name: 'mapSearch',
            component: MapSearch,
            meta: {
                title: '地图找店',
                breadcrumb: ['用户中心', '地图搜索']
            }
        },
        {
            path: 'shop/:id',
            name: 'shopDetail',
            component: ShopDetail,
            props: true,
            meta: {
                title: '商家详情',
                breadcrumb: ['用户中心', '商家详情']
            }
        },
        {
            path: 'collections',
            name: 'collectionManage',
            component: CollectionManage,
            meta: {
                title: '我的收藏',
                breadcrumb: ['用户中心', '收藏管理']
            }
        },
        {
            path: 'comments',
            name: 'userComments',
            component: UserComments,
            meta: {
                title: '我的评价',
                breadcrumb: ['用户中心', '我的评价']
            }
        },
        {
            path: 'assistant',
            name: 'intelligentAssistant',
            component: IntelligentAssistant,
            meta: {
                title: '智能助手',
                breadcrumb: ['用户中心', '智能助手']
            }
        },
        
        { path: '', redirect: { name: 'listSearch' } }
    ]
}
