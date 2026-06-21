import { describe, expect, it } from 'vitest';
import { withFayConnectionParams } from './fayConnectionParams';

describe('withFayConnectionParams', () => {
  it('appends Fay websocket auth params while preserving existing model query', () => {
    const url = withFayConnectionParams('http://127.0.0.1:5174?model=Natori', 'jwt-token', 'alice');

    expect(url).toBe('http://127.0.0.1:5174/?model=Natori&fay_token=jwt-token&fay_username=alice');
  });

  it('leaves render url unchanged when there is no auth token', () => {
    const url = withFayConnectionParams('http://127.0.0.1:5174?model=Natori', '', 'alice');

    expect(url).toBe('http://127.0.0.1:5174?model=Natori');
  });
});
