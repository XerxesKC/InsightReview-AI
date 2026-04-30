import Login from '@/views/Login.vue'
import UserRegister from '@/views/register/UserRegister.vue'
import MerchantRegister from '@/views/register/MerchantRegister.vue'

export default [
    {
        path: '/login',
        name: 'login',
        component: Login,
        meta: {
            public: true,
            title: '系统登录'
        }
    },
    {
        path: '/register',
        redirect: '/register/user',
        meta: { public: true }
    },
    {
        path: '/register/user',
        name: 'userRegister',
        component: UserRegister,
        meta: {
            public: true,
            title: '用户注册'
        }
    },
    {
        path: '/register/merchant',
        name: 'merchantRegister',
        component: MerchantRegister,
        meta: {
            public: true,
            title: '商家入驻'
        }
    }
]