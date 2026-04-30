import { createRouter, createWebHistory } from 'vue-router'

import authRoutes from './routes/auth'
import userRoute from './routes/user'
import merchantRoute from './routes/merchant'
import adminRoute from './routes/admin'

const routes = [
  ...authRoutes,

  userRoute,

  merchantRoute,

  adminRoute,

  {
    path: '/',
    redirect: '/login',
    meta: { hidden: true }
  },

  {
    path: '/:pathMatch(.*)*',
    component: () => import('@/views/PageNotFound.vue'),
    meta: {
      layout: 'empty'
    }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
