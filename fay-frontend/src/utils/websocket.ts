import type { WebsocketPayload } from '../types';

type MessageHandler = (payload: WebsocketPayload) => void;

export function getFayWebSocketUrl(defaultPort = '10003'): string {
  if (__FAY_WS_URL__) {
    return __FAY_WS_URL__;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.hostname}:${defaultPort}`;
}

export class ReconnectingSocket {
  private socket: WebSocket | null = null;
  private closedByUser = false;
  private connected = false;
  private reconnectTimer: number | null = null;
  private username = 'User';

  constructor(
    private readonly url: string,
    private readonly onMessage: MessageHandler,
    private readonly reconnectDelay = 5000,
  ) {}

  connect() {
    this.closedByUser = false;
    this.clearReconnectTimer();
    this.socket = new WebSocket(this.url);
    this.connected = false;
    this.socket.onopen = () => this.sendRegistration();
    this.socket.onmessage = (event) => this.handleMessage(event.data);
    this.socket.onclose = () => {
      this.connected = false;
      this.scheduleReconnect();
    };
    this.socket.onerror = () => this.socket?.close();
  }

  registerUsername(username: string) {
    this.username = username || 'User';
    if (this.connected) {
      this.sendRegistration();
    }
  }

  close() {
    this.closedByUser = true;
    this.connected = false;
    this.clearReconnectTimer();
    this.socket?.close();
    this.socket = null;
  }

  private sendRegistration() {
    this.connected = true;
    this.socket?.send(JSON.stringify({ Username: this.username }));
  }

  private handleMessage(raw: string) {
    try {
      this.onMessage(JSON.parse(raw));
    } catch (error) {
      console.warn('[Fay] 无法解析 WebSocket 消息', error);
    }
  }

  private scheduleReconnect() {
    if (this.closedByUser || this.reconnectTimer !== null) {
      return;
    }
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, this.reconnectDelay);
  }

  private clearReconnectTimer() {
    if (this.reconnectTimer === null) {
      return;
    }
    window.clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
  }
}
