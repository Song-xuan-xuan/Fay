import { describe, expect, it } from 'vitest';
import {
  ASSISTANT_AVATAR_SRC,
  BRAND_LOGO_SRC,
  DEFAULT_DIGITAL_HUMAN_COVER_SRC,
  DEFAULT_USER_AVATAR_SRC,
  FAVICON_SRC,
  FRONTEND_ASSET_PATHS,
  HTML2CANVAS_SCRIPT_SRC,
  MARKED_SCRIPT_SRC,
} from './assets';

describe('frontend asset paths', () => {
  it('keeps Vue-owned static assets under the frontend public route', () => {
    expect(FRONTEND_ASSET_PATHS).toEqual([
      BRAND_LOGO_SRC,
      FAVICON_SRC,
      DEFAULT_USER_AVATAR_SRC,
      ASSISTANT_AVATAR_SRC,
      DEFAULT_DIGITAL_HUMAN_COVER_SRC,
      MARKED_SCRIPT_SRC,
      HTML2CANVAS_SCRIPT_SRC,
    ]);

    for (const path of FRONTEND_ASSET_PATHS) {
      expect(path).toMatch(/^\/frontend-static\//);
      expect(path).not.toContain('/static/');
      expect(path).not.toContain('Fay_');
    }
  });
});
