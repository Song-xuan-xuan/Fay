import { describe, expect, it } from 'vitest';
import source from './Recommendation.vue?raw';

describe('Recommendation view navigation affordances', () => {
  it('keeps route recommendation and admin maintenance in the same recommendation workspace', () => {
    expect(source).toContain('recommendation-page-tabs');
    expect(source).toContain('路线推荐');
    expect(source).toContain('维护推荐');
    expect(source).toContain('to="/app/recommendation"');
    expect(source).toContain('to="/app/recommendation/manage"');
  });

  it('shows the maintenance entry only for administrators', () => {
    expect(source).toContain('useAuthStore');
    expect(source).toContain('authStore.isAdmin');
    expect(source).toMatch(/v-if="authStore\.isAdmin"[\s\S]*to="\/app\/recommendation\/manage"/);
  });

  it('keeps the visitor form limited to supported recommendation inputs', () => {
    expect(source).toContain('兴趣标签');
    expect(source).toContain('补充描述');
    expect(source).toContain('游览时长');
    expect(source).toContain('体力强度');
    expect(source).not.toContain('label="到达时间"');
    expect(source).not.toContain('label="起点"');
    expect(source).not.toContain('label="终点"');
    expect(source).not.toContain('label="预算"');
    expect(source).not.toContain('label="同行人"');
    expect(source).toContain('function recommendationPayload()');
  });

  it('offers useful preset actions instead of a blank recommendation result', () => {
    expect(source).toContain('recommendation-empty-state');
    expect(source).toContain('历史文化深度游');
    expect(source).toContain('自然风光轻松游');
    expect(source).toContain('亲子家庭经典游');
    expect(source).toContain('@click="applyPreset(preset)"');
    expect(source).not.toContain('<el-empty v-if="!result?.main_route"');
  });
});
