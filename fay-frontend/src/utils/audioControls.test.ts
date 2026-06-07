import { describe, expect, it } from 'vitest';
import { buildAudioConfigPatch, toggleAudioFlag } from './audioControls';

describe('audioControls', () => {
  it('toggles one audio flag without mutating the current config', () => {
    const current = { mic: true, speaker: false };
    const next = toggleAudioFlag(current, 'speaker');

    expect(next).toEqual({ mic: true, speaker: true });
    expect(current).toEqual({ mic: true, speaker: false });
  });

  it('builds the legacy submit payload for mic and speaker switches', () => {
    expect(buildAudioConfigPatch({ mic: false })).toEqual({
      source: { record: { enabled: false } },
    });
    expect(buildAudioConfigPatch({ speaker: true })).toEqual({
      interact: { playSound: true },
    });
  });
});
