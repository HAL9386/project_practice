import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { title: '系统概览', icon: 'Odometer' }
    },
    {
      path: '/prediction',
      name: 'prediction',
      component: () => import('../views/Prediction.vue'),
      meta: { title: '时间序列预测', icon: 'TrendCharts' }
    },
    {
      path: '/data-management',
      name: 'data-management',
      component: () => import('../views/DataManagement.vue'),
      meta: { title: '数据管理', icon: 'DataLine' }
    },
    {
      path: '/model-management',
      name: 'model-management',
      component: () => import('../views/ModelManagement.vue'),
      meta: { title: '模型管理', icon: 'SetUp' }
    },
    {
      path: '/task-history',
      name: 'task-history',
      component: () => import('../views/TaskHistory.vue'),
      meta: { title: '任务历史', icon: 'List' }
    },
    {
      path: '/user',
      name: 'user',
      component: () => import('../views/User.vue'),
      meta: { title: '用户中心', icon: 'User' }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { title: '登录', hidden: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/Register.vue'),
      meta: { title: '注册', hidden: true }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFound.vue'),
      meta: { title: '404', hidden: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 时间序列预测可视化系统` : '时间序列预测可视化系统'
  
  // 这里可以添加登录验证逻辑
  const isAuthenticated = localStorage.getItem('token')
  
  if (to.name !== 'login' && to.name !== 'register' && !isAuthenticated) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router