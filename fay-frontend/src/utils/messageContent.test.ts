import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  convertImagePaths,
  getImagePathFromClickTarget,
  parseAssistantContent,
  renderFallbackContent,
  renderMarkdownContent,
  trimContentLines,
} from './messageContent';

afterEach(() => {
  delete (globalThis as any).window;
});

describe('trimContentLines', () => {
  it('trims each line and drops empty lines', () => {
    expect(trimContentLines('  one  \n\n  two\t\n  ')).toBe('one\ntwo');
  });
});

describe('parseAssistantContent', () => {
  it('extracts complete think and prestart blocks while preserving main content', () => {
    const parsed = parseAssistantContent([
      '<think>',
      '  step one  ',
      '</think>',
      '最终回答',
      '<prestart data-tool="x">',
      '  D:\\tmp\\chart.png  ',
      '</prestart>',
    ].join('\n'));

    expect(parsed.thinkContent).toBe('step one');
    expect(parsed.mainContent).toBe('最终回答');
    expect(parsed.prestartContent).toBe('D:\\tmp\\chart.png');
    expect(parsed.isThinking).toBe(false);
  });

  it('treats an incomplete think block as in-progress thinking', () => {
    const parsed = parseAssistantContent('<think>\n  正在思考\n');

    expect(parsed.thinkContent).toBe('正在思考');
    expect(parsed.mainContent).toBe('');
    expect(parsed.isThinking).toBe(true);
  });

  it('returns trimmed main content when no control tags exist', () => {
    expect(parseAssistantContent('  hello  ').mainContent).toBe('hello');
  });
});

describe('convertImagePaths', () => {
  it('converts Windows image paths to clickable thumbnail html', () => {
    const html = convertImagePaths('see D:\\tmp\\a chart.png', 'http://127.0.0.1:5000');

    expect(html).toContain('/api/local-image?path=D%3A%5Ctmp%5Ca%20chart.png');
    expect(html).toContain('data-image-path="D%3A%5Ctmp%5Ca%20chart.png"');
    expect(html).toContain('D:/tmp/a chart.png');
  });

  it('escapes display paths before embedding them in html', () => {
    const html = convertImagePaths('D:\\tmp\\bad"quote.png', 'http://127.0.0.1:5000');

    expect(html).toContain('D:/tmp/bad&quot;quote.png');
    expect(html).not.toContain('D:/tmp/bad"quote.png');
  });
});

describe('getImagePathFromClickTarget', () => {
  it('extracts decoded image path from thumbnail container click target', () => {
    const container = {
      classList: { contains: (name: string) => name === 'image-thumbnail-container' },
      dataset: { imagePath: 'D%3A%5Ctmp%5Ca%20chart.png' },
      closest: () => null,
    } as unknown as HTMLElement;

    expect(getImagePathFromClickTarget(container)).toBe('D:\\tmp\\a chart.png');
  });

  it('walks up from thumbnail children and ignores unrelated targets', () => {
    const container = {
      classList: { contains: () => true },
      dataset: { imagePath: 'D%3A%5Ctmp%5Cb.png' },
    };
    const child = {
      classList: { contains: () => false },
      dataset: {},
      closest: () => container,
    } as unknown as HTMLElement;
    const unrelated = {
      classList: { contains: () => false },
      dataset: {},
      closest: () => null,
    } as unknown as HTMLElement;

    expect(getImagePathFromClickTarget(child)).toBe('D:\\tmp\\b.png');
    expect(getImagePathFromClickTarget(unrelated)).toBeNull();
  });
});

describe('renderFallbackContent', () => {
  it('escapes html and keeps line breaks', () => {
    const html = renderFallbackContent('<script>x</script>\\nsecond', 'http://127.0.0.1:5000');

    expect(html).toBe('&lt;script&gt;x&lt;/script&gt;<br>second');
  });
});

describe('renderMarkdownContent', () => {
  it('falls back to escaped rendering when marked is unavailable', () => {
    const html = renderMarkdownContent('<script>x</script>\\nsecond', 'http://127.0.0.1:5000');

    expect(html).toBe('&lt;script&gt;x&lt;/script&gt;<br>second');
  });

  it('uses marked with gfm breaks and still converts local image paths', () => {
    const marked = {
      setOptions: vi.fn(),
      parse: vi.fn().mockReturnValue('<p>**ok** D:\\tmp\\a.png</p>'),
    };
    (globalThis as any).window = { marked };

    const html = renderMarkdownContent('line one\\nline two', 'http://127.0.0.1:5000');

    expect(marked.setOptions).toHaveBeenCalledWith({ breaks: true, gfm: true });
    expect(marked.parse).toHaveBeenCalledWith('line one\nline two');
    expect(html).toContain('<p>**ok** ');
    expect(html).toContain('/api/local-image?path=D%3A%5Ctmp%5Ca.png');
  });
});
