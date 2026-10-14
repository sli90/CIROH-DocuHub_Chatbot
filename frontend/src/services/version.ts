// Detects that a newer release was deployed while this tab stayed open.
//
// Every build gives the main script a new content-hashed name
// (assets/index-<hash>.js). If the live index.html now points at a different
// one, this tab is running old code (e.g. without conversation memory) and
// should be refreshed.

const SCRIPT_PATTERN = /\/assets\/index-[\w-]+\.js/;

function runningScript(): string | null {
  const scripts = Array.from(document.querySelectorAll<HTMLScriptElement>('script[src]'));
  for (const script of scripts) {
    const match = new URL(script.src, window.location.href).pathname.match(SCRIPT_PATTERN);
    if (match) return match[0];
  }
  return null;
}

/** True if the deployed site has a newer build than the one running here.
 * Always false in development (`npm run dev` has no hashed bundle). */
export async function isNewVersionAvailable(
  isProduction: boolean = !!(import.meta as any).env?.PROD
): Promise<boolean> {
  if (!isProduction) return false;
  const current = runningScript();
  if (!current) return false;
  try {
    const response = await fetch('/index.html', { cache: 'no-store' });
    if (!response.ok) return false;
    const live = (await response.text()).match(SCRIPT_PATTERN)?.[0];
    return !!live && live !== current;
  } catch {
    return false;
  }
}
