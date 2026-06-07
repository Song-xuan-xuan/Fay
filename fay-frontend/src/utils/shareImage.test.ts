import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  DEFAULT_HTML2CANVAS_OPTIONS,
  downloadCanvas,
  exportElementAsImage,
  loadHtml2Canvas,
} from './shareImage';

class FakeElement {
  public async = false;
  public children: FakeElement[] = [];
  public download = '';
  public href = '';
  public onerror: ((event: Event) => void) | null = null;
  public onload: ((event: Event) => void) | null = null;
  public parent: FakeElement | null = null;
  public src = '';
  public readonly click = vi.fn();

  public constructor(public readonly tagName: string) {}

  public appendChild(child: FakeElement): FakeElement {
    child.parent = this;
    this.children.push(child);
    return child;
  }

  public dispatchEvent(event: Event): boolean {
    if (event.type === 'load') {
      this.onload?.(event);
    }
    if (event.type === 'error') {
      this.onerror?.(event);
    }
    return true;
  }

  public remove(): void {
    if (!this.parent) {
      return;
    }
    this.parent.children = this.parent.children.filter((child) => child !== this);
    this.parent = null;
  }

  public set innerHTML(value: string) {
    if (value === '') {
      this.children = [];
    }
  }
}

function installFakeDom() {
  const head = new FakeElement('head');
  const body = new FakeElement('body');
  const document = {
    body,
    head,
    createElement: (tagName: string) => new FakeElement(tagName),
    querySelector: (selector: string) => {
      const elements = [...head.children, ...body.children];
      if (selector === 'script[src="/static/js/html2canvas.min.js"]') {
        return elements.find((element) => element.tagName === 'script' && element.src === '/static/js/html2canvas.min.js') || null;
      }
      const download = selector.match(/^a\[download="(.+)"\]$/)?.[1];
      if (download) {
        return elements.find((element) => element.tagName === 'a' && element.download === download) || null;
      }
      return null;
    },
  };

  (globalThis as any).document = document;
  (globalThis as any).window = {};
  (globalThis as any).Event = class {
    public constructor(public readonly type: string) {}
  };
}

beforeEach(() => {
  installFakeDom();
});

afterEach(() => {
  delete window.html2canvas;
  document.body.innerHTML = '';
  vi.restoreAllMocks();
});

describe('shareImage', () => {
  it('returns existing html2canvas without injecting a script', async () => {
    const html2canvas = vi.fn();
    (window as any).html2canvas = html2canvas;

    await expect(loadHtml2Canvas()).resolves.toBe(html2canvas);
    expect(document.querySelector('script[src="/static/js/html2canvas.min.js"]')).toBeNull();
  });

  it('injects html2canvas script when the global function is missing', async () => {
    const promise = loadHtml2Canvas();
    const script = document.querySelector('script[src="/static/js/html2canvas.min.js"]') as HTMLScriptElement;

    expect(script).not.toBeNull();
    (window as any).html2canvas = vi.fn();
    script.dispatchEvent(new Event('load'));

    await expect(promise).resolves.toBe(window.html2canvas);
  });

  it('downloads a canvas png and removes the temporary link', () => {
    const canvas = { toDataURL: () => 'data:image/png;base64,abc' } as HTMLCanvasElement;

    downloadCanvas(canvas, 'fay_share_test.png');

    expect(document.querySelector('a[download="fay_share_test.png"]')).toBeNull();
  });

  it('exports an element using default html2canvas options', async () => {
    const element = document.createElement('div');
    const canvas = { toDataURL: () => 'data:image/png;base64,abc' } as HTMLCanvasElement;
    const html2canvas = vi.fn().mockResolvedValue(canvas);
    (window as any).html2canvas = html2canvas;

    await exportElementAsImage(element, 'fay_share_test.png');

    expect(html2canvas).toHaveBeenCalledWith(element, DEFAULT_HTML2CANVAS_OPTIONS);
  });
});
