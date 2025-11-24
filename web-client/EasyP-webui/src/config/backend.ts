const BACKEND_HOST = import.meta.env.VITE_BACKEND_HOST ?? '127.0.0.1';
const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT ?? '8010';
const HTTP_PROTOCOL = import.meta.env.VITE_BACKEND_HTTP_PROTOCOL ?? 'http';
const WS_PROTOCOL = import.meta.env.VITE_BACKEND_WS_PROTOCOL ?? (HTTP_PROTOCOL === 'https' ? 'wss' : 'ws');

const baseOrigin = import.meta.env.VITE_BACKEND_ORIGIN ?? `${HTTP_PROTOCOL}://${BACKEND_HOST}:${BACKEND_PORT}`;
const wsOrigin = import.meta.env.VITE_WEBSOCKET_ORIGIN ?? `${WS_PROTOCOL}://${BACKEND_HOST}:${BACKEND_PORT}`;

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? `${baseOrigin}/api`;
export const WEBSOCKET_URL = import.meta.env.VITE_WEBSOCKET_URL ?? `${wsOrigin}/ws/prompt`;
