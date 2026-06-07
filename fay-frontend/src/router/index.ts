import { createRouter, createWebHistory } from 'vue-router';
import AppLayout from '../layouts/AppLayout.vue';

const Message = () => import('../views/Message.vue');
const Setting = () => import('../views/Setting.vue');
const Live2D = () => import('../views/Live2D.vue');
const KnowledgeBase = () => import('../views/KnowledgeBase.vue');
const Mcp = () => import('../views/Mcp.vue');

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'message', component: Message },
        { path: 'setting', name: 'setting', component: Setting },
        { path: 'live2d', name: 'live2d', component: Live2D },
        { path: 'knowledge', name: 'knowledge', component: KnowledgeBase },
        { path: 'mcp', name: 'mcp', component: Mcp },
      ],
    },
  ],
});

export default router;
