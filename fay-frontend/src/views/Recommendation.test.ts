import { describe, expect, it } from 'vitest';
import source from './Recommendation.vue?raw';

describe('Recommendation view navigation affordances', () => {
  it('keeps route recommendation and admin maintenance in the same recommendation workspace', () => {
    expect(source).toContain('recommendation-page-tabs');
    expect(source).toContain('路线推荐');
    expect(source).toContain('维护推荐');
    expect(source).toContain('to="/recommendation"');
    expect(source).toContain('to="/recommendation/manage"');
  });

  it('shows the maintenance entry only for administrators', () => {
    expect(source).toContain('useAuthStore');
    expect(source).toContain('authStore.isAdmin');
    expect(source).toMatch(/v-if="authStore\.isAdmin"[\s\S]*to="\/recommendation\/manage"/);
  });
});
