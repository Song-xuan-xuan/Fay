type Html2Canvas = (element: HTMLElement, options: Html2CanvasOptions) => Promise<HTMLCanvasElement>;

interface Html2CanvasOptions {
  scale: number;
  useCORS: boolean;
  backgroundColor: string;
}

declare global {
  interface Window {
    html2canvas?: Html2Canvas;
  }
}

const HTML2CANVAS_SRC = '/static/js/html2canvas.min.js';
const IMAGE_MIME_TYPE = 'image/png';

export const DEFAULT_HTML2CANVAS_OPTIONS: Html2CanvasOptions = {
  scale: 2,
  useCORS: true,
  backgroundColor: '#ffffff',
};

function isHtml2Canvas(value: unknown): value is Html2Canvas {
  return typeof value === 'function';
}

export async function loadHtml2Canvas(): Promise<Html2Canvas> {
  if (isHtml2Canvas(window.html2canvas)) {
    return window.html2canvas;
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = HTML2CANVAS_SRC;
    script.async = true;
    script.onload = () => {
      if (isHtml2Canvas(window.html2canvas)) {
        resolve(window.html2canvas);
      } else {
        reject(new Error('html2canvas 未加载'));
      }
    };
    script.onerror = () => reject(new Error('html2canvas 加载失败'));
    document.head.appendChild(script);
  });
}

export function createShareImageFilename(now = Date.now()): string {
  return `fay_share_${now}.png`;
}

export function downloadCanvas(canvas: HTMLCanvasElement, filename: string): void {
  const link = document.createElement('a');
  link.download = filename;
  link.href = canvas.toDataURL(IMAGE_MIME_TYPE);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

export async function exportElementAsImage(element: HTMLElement, filename: string): Promise<void> {
  const html2canvas = await loadHtml2Canvas();
  const canvas = await html2canvas(element, DEFAULT_HTML2CANVAS_OPTIONS);
  downloadCanvas(canvas, filename);
}
