import { createRouter, createWebHistory } from 'vue-router';
import AppLayout from '../layouts/AppLayout.vue';
import { setupAuthGuards } from './guards';

const Login = () => import('../views/Login.vue');
const Message = () => import('../views/Message.vue');
const Setting = () => import('../views/Setting.vue');
const Live2D = () => import('../views/Live2D.vue');
const Dashboard = () => import('../views/Dashboard.vue');
const VisitorReport = () => import('../views/VisitorReport.vue');
const Recommendation = () => import('../views/Recommendation.vue');
const RecommendationManage = () => import('../views/RecommendationManage.vue');
const KnowledgeBase = () => import('../views/KnowledgeBase.vue');
const Mcp = () => import('../views/Mcp.vue');
const UserManagement = () => import('../views/UserManagement.vue');

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: Login, meta: { requiresAuth: false, public: true } },
    {
      path: '/',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'message', component: Message, meta: { requiresAuth: true } },
        { path: 'setting', name: 'setting', component: Setting, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'live2d', name: 'live2d', component: Live2D, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'dashboard', name: 'dashboard', component: Dashboard, meta: { requiresAuth: true } },
        { path: 'visitor-report', name: 'visitor-report', component: VisitorReport, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'recommendation', name: 'recommendation', component: Recommendation, meta: { requiresAuth: true } },
        { path: 'recommendation/manage', name: 'recommendation-manage', component: RecommendationManage, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'knowledge', name: 'knowledge', component: KnowledgeBase, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'mcp', name: 'mcp', component: Mcp, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'users', name: 'users', component: UserManagement, meta: { requiresAuth: true, requiresRole: 'admin' } },
      ],
    },
  ],
});

setupAuthGuards(router);

export default router;
