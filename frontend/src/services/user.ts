// The email a visitor signed in with. Required to ask questions: the
// backend limits each email to a fixed number of questions per day.

const EMAIL_KEY = 'ciroh_chat_email';

// Mirrors backend/rag/quota.py normalize_email.
const EMAIL_PATTERN = /^[^@\s]{1,64}@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$/;

export function normalizeEmail(raw: string): string | null {
  const email = raw.trim().toLowerCase();
  if (email.length > 254 || !EMAIL_PATTERN.test(email)) return null;
  return email;
}

export function getEmail(): string | null {
  try {
    return localStorage.getItem(EMAIL_KEY);
  } catch {
    return null;
  }
}

export function setEmail(email: string): void {
  try {
    localStorage.setItem(EMAIL_KEY, email);
  } catch {
    // Private mode: the email lasts for this page view only.
  }
}

export function clearEmail(): void {
  try {
    localStorage.removeItem(EMAIL_KEY);
  } catch {
    // Ignore.
  }
}
