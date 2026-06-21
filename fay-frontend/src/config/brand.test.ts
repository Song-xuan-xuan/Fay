import { describe, expect, it } from 'vitest';
import {
  BRAND_ASSISTANT_NAME,
  BRAND_CONSOLE_EYEBROW,
  BRAND_CONSOLE_NAME,
  BRAND_NAME,
  BRAND_PRODUCT_TAGLINE,
  BRAND_SERVICE_NAME,
  applyBrandDocumentTitle,
} from './brand';

describe('brand config', () => {
  it('derives visible product names from one brand name', () => {
    expect(BRAND_NAME).toBe('境语 AI');
    expect(BRAND_CONSOLE_NAME).toBe(`${BRAND_NAME} 管理台`);
    expect(BRAND_CONSOLE_EYEBROW).toContain('Console');
    expect(BRAND_ASSISTANT_NAME).toBe(BRAND_NAME);
    expect(BRAND_SERVICE_NAME).toBe(`${BRAND_NAME} 服务`);
    expect(BRAND_PRODUCT_TAGLINE).toContain('AI 数字人');
  });

  it('can apply the brand name to the document title', () => {
    const documentLike = { title: '' };
    applyBrandDocumentTitle(documentLike);
    expect(documentLike.title).toBe(BRAND_CONSOLE_NAME);
  });
});
