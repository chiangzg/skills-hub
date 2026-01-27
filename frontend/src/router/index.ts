import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 路由守卫
const guards = (to: any, from: any, next: any) => {
  // 检查是否需要认证
  const requiresAuth = to.meta.requiresAuth
  const requiresAdmin = to.meta.requiresAdmin

  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')

  if (requiresAuth && !token) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (requiresAdmin && userRole !== 'admin') {
    next({ name: 'home' })
    return
  }

  next()
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/categories',
    name: 'categories',
    component: () => import('../views/Category.vue')
  },
  {
    path: '/skills/:id',
    name: 'skill',
    component: () => import('../views/Skill.vue')
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../views/admin/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(guards as any)

export default router
