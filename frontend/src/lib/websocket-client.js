import { getAccessToken } from "./api-client";
import { getWsUrl } from "./app-config";

class WebSocketClient {
  ws = null;
  listeners = new Map();
  reconnectAttempts = 0;
  maxReconnectDelay = 30000;
  reconnectTimer = null;
  intentionalClose = false;

  connect() {
    const token = getAccessToken();
    if (!token) return;

    const wsUrl = getWsUrl();
    this.intentionalClose = false;

    try {
      this.ws = new WebSocket(`${wsUrl}/ws?token=${token}`);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          const eventType = parsed.type;
          if (eventType && this.listeners.has(eventType)) {
            this.listeners.get(eventType).forEach((cb) => cb(parsed.data));
          }
          if (this.listeners.has("*")) {
            this.listeners.get("*").forEach((cb) => cb(parsed));
          }
        } catch {}
      };

      this.ws.onclose = () => {
        if (!this.intentionalClose) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {}
  }

  scheduleReconnect() {
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType).add(callback);
  }

  off(eventType, callback) {
    this.listeners.get(eventType)?.delete(callback);
  }

  close() {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    this.ws?.close();
    this.ws = null;
  }
}

export const wsClient = new WebSocketClient();
