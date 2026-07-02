/** API and WebSocket base URLs (local dev defaults). */
export function getApiUrl() {
  const url = import.meta.env.VITE_API_URL || "http://localhost:8000";
  return url.replace(/\/$/, "");
}

export function getWsUrl() {
  const url = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
  return url.replace(/\/$/, "");
}
