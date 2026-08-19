import { API_CONFIG } from '../config/api';

const SESSION_KEY = 'ciroh_chat_session_id';

function randomId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `sess-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getSessionId(): string {
  try {
    const existing = localStorage.getItem(SESSION_KEY);
    if (existing) return existing;
    const created = randomId();
    localStorage.setItem(SESSION_KEY, created);
    return created;
  } catch {
    return randomId();
  }
}

export function trackEvent(event: string, payload: Record<string, unknown> = {}): void {
  const body = {
    session_id: getSessionId(),
    event,
    payload,
  };

  fetch(`${API_CONFIG.BASE_URL}/telemetry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).catch(() => {
    // Telemetry must never break chat.
  });
}
