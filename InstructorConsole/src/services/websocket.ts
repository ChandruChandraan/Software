type MessageCallback = (data: any) => void;
type ConnectionCallback = (connected: boolean) => void;

export class ConsoleWebSocketService {
  private socket: WebSocket | null = null;
  private listeners: Set<MessageCallback> = new Set();
  private connectionListeners: Set<ConnectionCallback> = new Set();
  private reconnectInterval: number = 3000;
  private url: string;
  private _isConnected: boolean = false;

  constructor(url?: string) {
    this.url = url || (import.meta as any).env?.VITE_WS_URL || 'ws://127.0.0.1:8000/ws/console';
  }

  get isConnected(): boolean {
    return this._isConnected;
  }

  connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        this._isConnected = true;
        this.connectionListeners.forEach((cb) => cb(true));
      };

      this.socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          this.listeners.forEach((cb) => cb(parsed));
        } catch {
          this.listeners.forEach((cb) => cb(event.data));
        }
      };

      this.socket.onclose = () => {
        this._isConnected = false;
        this.connectionListeners.forEach((cb) => cb(false));
        setTimeout(() => this.connect(), this.reconnectInterval);
      };

      this.socket.onerror = () => {
        this._isConnected = false;
        this.connectionListeners.forEach((cb) => cb(false));
        if (this.socket) {
          this.socket.close();
        }
      };
    } catch {
      this._isConnected = false;
      this.connectionListeners.forEach((cb) => cb(false));
      setTimeout(() => this.connect(), this.reconnectInterval);
    }
  }

  subscribe(callback: MessageCallback): () => void {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  onConnectionChange(callback: ConnectionCallback): () => void {
    this.connectionListeners.add(callback);
    callback(this._isConnected);
    return () => this.connectionListeners.delete(callback);
  }

  send(data: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this._isConnected = false;
      this.connectionListeners.forEach((cb) => cb(false));
    }
  }
}

export const consoleWs = new ConsoleWebSocketService();
