import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { isNewVersionAvailable } from './version';

const page = (script: string) => `<html><head><script type="module" src="${script}"></script></head></html>`;

describe('isNewVersionAvailable', () => {
  beforeEach(() => {
    const script = document.createElement('script');
    script.src = '/assets/index-OLD123.js';
    document.head.appendChild(script);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    document.head.innerHTML = '';
  });

  it('is true when the live index.html points at a different build', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(page('/assets/index-NEW456.js')));
    expect(await isNewVersionAvailable(true)).toBe(true);
  });

  it('is false when the build is current', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(page('/assets/index-OLD123.js')));
    expect(await isNewVersionAvailable(true)).toBe(false);
  });

  it('is false when the check fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('offline'));
    expect(await isNewVersionAvailable(true)).toBe(false);
  });

  it('never fires in development', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    expect(await isNewVersionAvailable(false)).toBe(false);
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
