import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ReconnectingSocket, getFayWebSocketUrl } from './websocket';

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];

  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onopen: (() => void) | null = null;
  sent: string[] = [];

  constructor(public readonly url: string) {
    FakeWebSocket.instances.push(this);
  }

  send(message: string) {
    this.sent.push(message);
  }

  close() {
    this.onclose?.();
  }

  open() {
    this.onopen?.();
  }
}

describe('ReconnectingSocket', () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('registers the selected username on open and when it changes', () => {
    const socket = new ReconnectingSocket('ws://localhost:10003', () => undefined);

    socket.connect();
    socket.registerUsername('Alice');
    FakeWebSocket.instances[0].open();
    socket.registerUsername('Bob');

    expect(FakeWebSocket.instances[0].sent.map((message) => JSON.parse(message))).toEqual([
      { Username: 'Alice' },
      { Username: 'Bob' },
    ]);
  });

  it('includes the latest auth token in registration messages', () => {
    let token = 'token-1';
    const socket = new ReconnectingSocket('ws://localhost:10003', () => undefined, 5000, () => token);

    socket.connect();
    socket.registerUsername('Alice');
    FakeWebSocket.instances[0].open();
    token = 'token-2';
    socket.registerUsername('Alice');

    expect(FakeWebSocket.instances[0].sent.map((message) => JSON.parse(message))).toEqual([
      { Username: 'Alice', token: 'token-1' },
      { Username: 'Alice', token: 'token-2' },
    ]);
  });
});

describe('getFayWebSocketUrl', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('uses the local Fay websocket port on localhost', () => {
    vi.stubGlobal('window', {
      location: new URL('http://localhost:5173/'),
    });

    expect(getFayWebSocketUrl()).toBe('ws://localhost:10003');
  });

  it('uses the Caddy websocket path on deployed hosts', () => {
    vi.stubGlobal('window', {
      location: new URL('https://fay.songtf.cn/'),
    });

    expect(getFayWebSocketUrl()).toBe('wss://fay.songtf.cn/ws-ui');
  });
});
