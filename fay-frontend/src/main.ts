import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';

import App from './App.vue';
import { applyBrandDocumentTitle } from './config/brand';
import router from './router';
import './styles/main.css';

applyBrandDocumentTitle();
createApp(App).use(createPinia()).use(router).use(ElementPlus).mount('#app');
