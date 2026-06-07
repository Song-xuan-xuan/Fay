interface MarkedApi {
  setOptions: (options: { breaks: boolean; gfm: boolean }) => void;
  parse: (content: string) => string;
}

declare global {
  interface Window {
    marked?: MarkedApi;
  }
}

const MARKED_SRC = '/static/js/marked.min.js';

function isMarkedApi(value: unknown): value is MarkedApi {
  const api = value as Partial<MarkedApi> | undefined;
  return typeof api?.parse === 'function' && typeof api?.setOptions === 'function';
}

export function getMarked(): MarkedApi | null {
  return isMarkedApi(window.marked) ? window.marked : null;
}

export async function loadMarked(): Promise<MarkedApi> {
  const current = getMarked();
  if (current) {
    return current;
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = MARKED_SRC;
    script.async = true;
    script.onload = () => {
      const marked = getMarked();
      if (marked) {
        resolve(marked);
      } else {
        reject(new Error('marked 未加载'));
      }
    };
    script.onerror = () => reject(new Error('marked 加载失败'));
    document.head.appendChild(script);
  });
}
