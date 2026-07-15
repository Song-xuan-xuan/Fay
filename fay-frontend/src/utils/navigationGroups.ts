export type PrimaryNavigationKey = 'home' | 'message' | 'knowledge' | 'digital-human' | 'recommendation' | 'data' | 'settings';

export interface PrimaryNavigationGroup {
  key: PrimaryNavigationKey;
  label: string;
  to: string;
  activePaths: string[];
  public?: boolean;
  requiresRole?: 'admin';
}

const primaryNavigationGroups: PrimaryNavigationGroup[] = [
  { key: 'home', label: '首页', to: '/', activePaths: ['/'], public: true },
  { key: 'message', label: '对话', to: '/app/chat', activePaths: ['/app/chat'] },
  { key: 'knowledge', label: '知识', to: '/app/knowledge', activePaths: ['/app/knowledge'], requiresRole: 'admin' },
  { key: 'digital-human', label: '数字人', to: '/app/live2d', activePaths: ['/app/live2d'], requiresRole: 'admin' },
  { key: 'recommendation', label: '推荐', to: '/app/recommendation', activePaths: ['/app/recommendation', '/app/recommendation/manage'] },
  {
    key: 'data',
    label: '数据',
    to: '/app/dashboard',
    activePaths: ['/app/dashboard', '/app/visitor-report'],
  },
  { key: 'settings', label: '设置', to: '/app/settings', activePaths: ['/app/settings', '/app/users'], requiresRole: 'admin' },
];

export function getPrimaryNavigationGroups() {
  return primaryNavigationGroups;
}

export function isNavigationGroupActive(path: string, group: PrimaryNavigationGroup) {
  if (group.key === 'home') {
    return path === '/';
  }
  return group.activePaths.some((activePath) => {
    return path === activePath || path.startsWith(`${activePath}/`);
  });
}
