export interface NavMatchOptions {
  to: string;
  exact?: boolean;
}

function normalizePath(path: string) {
  const normalized = path.trim() || '/';
  if (normalized === '/') return normalized;
  return normalized.replace(/\/+$/, '');
}

export function isNavItemActive(currentPath: string, item: NavMatchOptions) {
  const path = normalizePath(currentPath);
  const target = normalizePath(item.to);

  if (item.exact) {
    return path === target;
  }

  return path === target || path.startsWith(`${target}/`);
}
