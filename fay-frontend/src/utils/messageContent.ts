export interface ParsedAssistantContent {
  thinkContent: string;
  mainContent: string;
  prestartContent: string;
  isThinking: boolean;
}

const IMAGE_PATH_REGEX = /([A-Za-z]:[\\\/][^\r\n<>'`]+\.(png|jpg|jpeg|gif|bmp|webp))/gi;
const IMAGE_CONTAINER_CLASS = 'image-thumbnail-container';
const MARKDOWN_OPTIONS = { breaks: true, gfm: true };

interface MarkedWindow {
  marked?: {
    setOptions: (options: typeof MARKDOWN_OPTIONS) => void;
    parse: (content: string) => string;
  };
}

export function trimContentLines(rawContent: string): string {
  return rawContent
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .join('\n');
}

export function parseAssistantContent(content = ''): ParsedAssistantContent {
  if (!content) {
    return { thinkContent: '', mainContent: '', prestartContent: '', isThinking: false };
  }

  let mainContent = content;
  let prestartContent = '';
  const prestartMatch = mainContent.match(/<prestart(?:[^>]*)>([\s\S]*)<\/prestart>/i);
  if (prestartMatch?.[1]) {
    prestartContent = trimContentLines(prestartMatch[1]);
    mainContent = mainContent.replace(/<prestart(?:[^>]*)>[\s\S]*<\/prestart>/gi, '');
  }

  const completeThinkMatch = mainContent.match(/<think>([\s\S]*?)<\/think>/i);
  if (completeThinkMatch?.[1]) {
    return {
      thinkContent: trimContentLines(completeThinkMatch[1]),
      mainContent: mainContent.replace(/<think>[\s\S]*?<\/think>/i, '').trim(),
      prestartContent,
      isThinking: false,
    };
  }

  const incompleteThinkMatch = mainContent.match(/<think>([\s\S]*)/i);
  if (incompleteThinkMatch?.[1]) {
    return {
      thinkContent: trimContentLines(incompleteThinkMatch[1]),
      mainContent: '',
      prestartContent,
      isThinking: true,
    };
  }

  return {
    thinkContent: '',
    mainContent: mainContent.trim(),
    prestartContent,
    isThinking: false,
  };
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function convertImagePaths(content: string, baseUrl = window.location.origin): string {
  if (!content) {
    return content;
  }

  return content.replace(IMAGE_PATH_REGEX, (match) => {
    const trimmedPath = match.trim();
    const encodedPath = encodeURIComponent(trimmedPath);
    const imgSrc = `${baseUrl}/api/local-image?path=${encodedPath}`;
    const displayPath = escapeHtml(trimmedPath.replace(/\\/g, '/'));
    return `<span class="image-thumbnail-container" data-image-path="${encodedPath}">` +
      `<img src="${imgSrc}" class="message-image-thumbnail" alt="图片" />` +
      `<span class="image-zoom-hint">点击查看</span>` +
      `<span class="image-path-text">${displayPath}</span>` +
      '</span>';
  });
}

function getImageContainer(target: HTMLElement): HTMLElement | null {
  if (target.classList?.contains(IMAGE_CONTAINER_CLASS)) {
    return target;
  }
  return target.closest?.(`.${IMAGE_CONTAINER_CLASS}`) as HTMLElement | null;
}

export function getImagePathFromClickTarget(target: EventTarget | null): string | null {
  if (!target || typeof (target as HTMLElement).closest !== 'function') {
    return null;
  }
  const container = getImageContainer(target as HTMLElement);
  const encodedPath = container?.dataset.imagePath;
  return encodedPath ? decodeURIComponent(encodedPath) : null;
}

export function renderFallbackContent(content: string, baseUrl = window.location.origin): string {
  if (!content) {
    return '';
  }
  const escaped = escapeHtml(content)
    .replace(/\\n/g, '<br>')
    .replace(/\n/g, '<br>');
  return convertImagePaths(escaped, baseUrl);
}

function getMarkedParser() {
  return (globalThis as { window?: MarkedWindow }).window?.marked;
}

export function renderMarkdownContent(
  content: string,
  baseUrl = window.location.origin,
  _renderVersion = 0,
): string {
  const marked = getMarkedParser();
  if (!content || !marked?.parse || !marked.setOptions) {
    return renderFallbackContent(content, baseUrl);
  }
  try {
    marked.setOptions(MARKDOWN_OPTIONS);
    const escaped = escapeHtml(content).replace(/\\n/g, '\n');
    return convertImagePaths(marked.parse(escaped), baseUrl);
  } catch {
    return renderFallbackContent(content, baseUrl);
  }
}
