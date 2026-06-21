export const BRAND_NAME = '境语 AI';
export const BRAND_EN_NAME = 'Jingyu AI';
export const BRAND_CONSOLE_NAME = `${BRAND_NAME} 管理台`;
export const BRAND_CONSOLE_EYEBROW = `${BRAND_EN_NAME} Console`;
export const BRAND_PRODUCT_TAGLINE = '面向景区与展馆的 AI 数字人知识服务平台';
export const BRAND_ASSISTANT_NAME = BRAND_NAME;
export const BRAND_SERVICE_NAME = `${BRAND_NAME} 服务`;
export const BRAND_SHARE_TITLE = `${BRAND_NAME} 数字人服务平台`;
export const BRAND_SHARE_FOOTER = BRAND_PRODUCT_TAGLINE;

export function applyBrandDocumentTitle(target: { title: string } = document) {
  target.title = BRAND_CONSOLE_NAME;
}
