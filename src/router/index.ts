import { createRouter, createWebHistory } from 'vue-router'
import DatasetManager from '../views/DatasetManager.vue'
import TrainingManager from '../views/TrainingManager.vue'
import ModelManager from '../views/ModelManager.vue'
import LogViewer from '../views/LogViewer.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      redirect: '/datasets' // 默认重定向到数据集管理
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/datasets',
      name: 'datasets',
      component: DatasetManager
    },
    {
      path: '/training',
      name: 'training',
      component: TrainingManager
    },
    {
      path: '/models',
      name: 'models',
      component: ModelManager
    },
    {
      path: '/logs',
      name: 'logs',
      component: LogViewer
    },
  ]
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const authToken = localStorage.getItem('authToken');
  const isAuthenticated = authToken === 'authenticated'; // 只有真实登录才允许
  
  // 如果访问登录页且已登录，重定向到首页
  if (to.name === 'login' && isAuthenticated) {
    next({ name: 'home' });
    return;
  }
  
  // 如果访问非登录页且未登录，重定向到登录页
  if (to.name !== 'login' && !isAuthenticated) {
    // 清除可能存在的无效 token
    if (authToken && authToken !== 'authenticated') {
      localStorage.removeItem('authToken');
      localStorage.removeItem('userId');
    }
    next({ name: 'login' });
    return;
  }
  
  next();
});

export default router

