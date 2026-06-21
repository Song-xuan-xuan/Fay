export type PrimaryNavigationKey = 'message' | 'knowledge' | 'digital-human' | 'data' | 'settings';

export interface PrimaryNavigationGroup {
  key: PrimaryNavigationKey;
  label: string;
  to: string;
  activePaths: string[];
  requiresRole?: 'admin';
}

const primaryNavigationGroups: PrimaryNavigationGroup[] = [
  { key: 'message', label: '对话', to: '/', activePaths: ['/'] },
  { key: 'knowledge', label: '知识', to: '/knowledge', activePaths: ['/knowledge'], requiresRole: 'admin' },
  { key: 'digital-human', label: '数字人', to: '/live2d', activePaths: ['/live2d'], requiresRole: 'admin' },
  {
    key: 'data',
    label: '数据',
    to: '/dashboard',
    activePaths: ['/dashboard', '/visitor-report', '/recommendation', '/recommendation/manage'],
  },
  { key: 'settings', label: '设置', to: '/mcp', activePaths: ['/mcp', '/users', '/setting'], requiresRole: 'admin' },
];

export function getPrimaryNavigationGroups() {
  return primaryNavigationGroups;
}

export function isNavigationGroupActive(path: string, group: PrimaryNavigationGroup) {
  return group.activePaths.some((activePath) => {
    if (activePath === '/') {
      return path === '/';
    }
    return path === activePath || path.startsWith(`${activePath}/`);
  });
}
