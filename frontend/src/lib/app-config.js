/** API and WebSocket base URLs for local dev and production. */
const PRODUCTION_WS = "wss://booknest-api-xhkb.onrender.com";

function isLocalHost() {
  if (typeof window === "undefined") return false;
  return /localhost|127\.0\.0\.1/.test(window.location.hostname);
}

export function getApiUrl() {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) return envUrl.replace(/\/$/, "");
  // Same-origin /api proxy on Vercel (see vercel.json)
  if (!isLocalHost()) return `${window.location.origin}/api`;
  return "http://localhost:8000";
}

export function getWsUrl() {
  const envUrl = import.meta.env.VITE_WS_URL;
  if (envUrl) return envUrl.replace(/\/$/, "");
  if (!isLocalHost()) return PRODUCTION_WS;
  return "ws://localhost:8000";
}
