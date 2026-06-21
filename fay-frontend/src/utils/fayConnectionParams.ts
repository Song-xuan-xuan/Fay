const FAY_TOKEN_PARAM = 'fay_token';
const FAY_USERNAME_PARAM = 'fay_username';
const RELATIVE_URL_BASE = 'http://fay.local';

function isRelativeUrl(url: string) {
  return url.startsWith('/') && !url.startsWith('//');
}

export function withFayConnectionParams(renderUrl: string, token: string, username = 'User') {
  const trimmedUrl = renderUrl.trim();
  const trimmedToken = token.trim();
  if (!trimmedUrl || !trimmedToken) {
    return renderUrl;
  }

  try {
    const relative = isRelativeUrl(trimmedUrl);
    const url = new URL(trimmedUrl, RELATIVE_URL_BASE);
    url.searchParams.set(FAY_TOKEN_PARAM, trimmedToken);
    if (username.trim()) {
      url.searchParams.set(FAY_USERNAME_PARAM, username.trim());
    }
    if (relative) {
      return `${url.pathname}${url.search}${url.hash}`;
    }
    return url.toString();
  } catch {
    return renderUrl;
  }
}
