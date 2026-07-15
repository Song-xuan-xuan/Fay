import { createRouter, createWebHistory } from 'vue-router';
import AppLayout from '../layouts/AppLayout.vue';
import { setupAuthGuards } from './guards';

const Login = () => import('../views/Login.vue');
const Home = () => import('../views/Home.vue');
const Message = () => import('../views/Message.vue');
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
    {
      path: '/',
      component: AppLayout,
      meta: { requiresAuth: false, public: true },
      children: [
        { path: '', name: 'home', component: Home, meta: { requiresAuth: false, public: true } },
      ],
    },
    { path: '/login', name: 'login', component: Login, meta: { requiresAuth: false, public: true } },
    {
      path: '/app',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/app/chat' },
        { path: 'chat', name: 'message', component: Message, meta: { requiresAuth: true } },
        { path: 'live2d', name: 'live2d', component: Live2D, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'dashboard', name: 'dashboard', component: Dashboard, meta: { requiresAuth: true } },
        { path: 'visitor-report', name: 'visitor-report', component: VisitorReport, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'recommendation', name: 'recommendation', component: Recommendation, meta: { requiresAuth: true } },
        { path: 'recommendation/manage', name: 'recommendation-manage', component: RecommendationManage, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'knowledge', name: 'knowledge', component: KnowledgeBase, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'settings', name: 'mcp', component: Mcp, meta: { requiresAuth: true, requiresRole: 'admin' } },
        { path: 'users', name: 'users', component: UserManagement, meta: { requiresAuth: true, requiresRole: 'admin' } },
      ],
    },
    { path: '/setting', redirect: '/app/live2d' },
    { path: '/live2d', redirect: '/app/live2d' },
    { path: '/dashboard', redirect: '/app/dashboard' },
    { path: '/visitor-report', redirect: '/app/visitor-report' },
    { path: '/recommendation', redirect: '/app/recommendation' },
    { path: '/recommendation/manage', redirect: '/app/recommendation/manage' },
    { path: '/knowledge', redirect: '/app/knowledge' },
    { path: '/mcp', redirect: '/app/settings' },
    { path: '/users', redirect: '/app/users' },
  ],
});

setupAuthGuards(router);

export default router;
