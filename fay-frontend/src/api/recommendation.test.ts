import { beforeEach, describe, expect, it, vi } from 'vitest';
import request from './request';
import {
  createRecommendationEdge,
  createRecommendation,
  deleteRecommendationEdge,
  listRecommendationAttractions,
  listRecommendationEdges,
  saveRecommendationPreferences,
} from './recommendation';

vi.mock('./request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('recommendation api', () => {
  beforeEach(() => {
    vi.mocked(request.get).mockReset();
    vi.mocked(request.post).mockReset();
    vi.mocked(request.put).mockReset();
  });

  it('posts recommendation requests to the standalone entry', () => {
    createRecommendation({ interests: ['history'], time_budget_minutes: 120 });

    expect(request.post).toHaveBeenCalledWith(
      '/api/recommendation/recommend',
      { interests: ['history'], time_budget_minutes: 120 },
      { timeout: 120000 },
    );
  });

  it('saves preferences for the logged-in visitor', () => {
    saveRecommendationPreferences({ interests: ['nature'] });

    expect(request.put).toHaveBeenCalledWith('/api/recommendation/preferences', { interests: ['nature'] });
  });

  it('loads admin attraction records', () => {
    listRecommendationAttractions();

    expect(request.get).toHaveBeenCalledWith('/api/recommendation/admin/attractions');
  });

  it('manages admin route edges', () => {
    listRecommendationEdges();
    createRecommendationEdge({ from_attraction_id: 1, to_attraction_id: 2, walk_minutes: 8 });
    deleteRecommendationEdge(3);

    expect(request.get).toHaveBeenCalledWith('/api/recommendation/admin/edges');
    expect(request.post).toHaveBeenCalledWith('/api/recommendation/admin/edges', {
      from_attraction_id: 1,
      to_attraction_id: 2,
      walk_minutes: 8,
    });
    expect(request.delete).toHaveBeenCalledWith('/api/recommendation/admin/edges/3');
  });
});
