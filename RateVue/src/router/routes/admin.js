import AdminLayout from '@/layouts/AdminLayout.vue'

const UserManagement = () => import('@/views/admin/UserManagement.vue')
const commentManagement = () => import('@/views/Admin/CommentManagement.vue')
const MerchantManagement = () => import('@/views/admin/MerchantManagement.vue')
const DataAnalysis = () => import('@/views/admin/DataAnalysis.vue')
const KnowledgeBaseManagement = () => import('@/views/Admin/KnowledgeBaseManagement.vue')
const DocumentWorkbench = () => import('@/views/admin/DocumentWorkbench.vue')
const NewDocumentWorkbench = () => import('@/views/admin/NewDocumentWorkbench.vue')
const SystemManagement = () => import('@/views/Admin/SystemManagement.vue')
const DocumentManagement = () => import('@/views/Admin/DocumentManagement.vue')
const DialogueLog = () => import('@/views/Admin/DialogueLog.vue')
const PandasAnalyzer = () => import('@/views/Admin/PandasAnalyzer.vue')
export default {
    path: '/admin',
    component: AdminLayout,
    meta: {
        requiresAuth: true,
        role: 'admin',
        breadcrumb: ['管理后台']
    },
    children: [
        {
            path: 'users',
            name: 'userManagement',
            component: UserManagement,
            meta: {
                title: '用户管理',
                keepAlive: true,
                breadcrumb: ['管理后台', '用户管理']
            }
        },
        {
            path: 'comment',
            name: 'commentManagement',
            component: commentManagement,
            meta: {
                title: '评论管理',
                keepAlive: true,
                breadcrumb: ['管理后台', '评论管理']
            }
        },
        {
            path: 'merchants',
            name: 'merchantManagement',
            component: MerchantManagement,
            meta: {
                title: '商家管理',
                keepAlive: true,
                breadcrumb: ['管理后台', '商家管理']
            }
        },
        {
            path: 'analytics',
            name: 'dataAnalysis',
            component: DataAnalysis,
            meta: {
                title: '系统分析',
                breadcrumb: ['管理后台', '数据分析']
            }
        },
        {
            path: 'doc-workbench',
            name: 'documentWorkbench',
            component: DocumentWorkbench,
            meta: {
                title: '文档审核与加工工作台',
                requiresAuth: true,
                role: 'admin',
                breadcrumb: ['管理后台', '文档工作台']
            }
        },
        {
            path: 'knowledge-base',
            name: 'knowledgeBaseManagement',
            component: KnowledgeBaseManagement,
            meta: {
                title: '知识库管理',
                breadcrumb: ['管理后台', '知识库管理']
            }
        },
        {
            path: 'system',
            name: 'systemManagement',
            component: SystemManagement,
            meta: {
                title: '系统管理',
                breadcrumb: ['管理后台', '系统管理']
            }
        },
        {
            path: 'documents',
            name: 'documentManagement',
            component: DocumentManagement,
            meta: {
                title: '平台手册管理',
                breadcrumb: ['管理后台', '平台手册管理']
            }
        },
        {
            path: 'dialogue-log',
            name: 'DialogueLog',
            component: DialogueLog,
            meta: {
                title: '对话日志',
                breadcrumb: ['用户中心', '对话日志']
            }
        },
        {
            path: 'new-doc-workbench',
            name: 'newDocumentWorkbench',
            component: NewDocumentWorkbench,
            meta: {
                title: '智能文档拆分',
                requiresAuth: true,
                role: 'admin',
                breadcrumb: ['管理后台', '智能文档拆分']
            }
        },
        {
            path: 'pandas-analyzer',
            name: 'pandasAnalyzer',
            component: PandasAnalyzer,
            meta: {
                title: 'Pandas分析器',
                requiresAuth: true,
                role: 'admin',
                breadcrumb: ['管理后台', 'Pandas分析器']
            }
        },
        { path: '', redirect: { name: 'userManagement' } }
    ]
}
