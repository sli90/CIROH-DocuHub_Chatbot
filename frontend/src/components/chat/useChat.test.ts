import { describe, it, expect } from 'vitest';
import { buildHistory } from './useChat';
import type { Message } from './types';

let nextId = 0;
const user = (text: string): Message => ({ id: String(nextId++), text, isBot: false, timestamp: new Date() });
const bot = (text: string, route?: string, extra: Partial<Message> = {}): Message => ({
  id: String(nextId++),
  text,
  isBot: true,
  timestamp: new Date(),
  route,
  ...extra,
});

describe('buildHistory', () => {
  it('returns question/answer pairs in order', () => {
    expect(buildHistory([user('What is NGIAB?'), bot('NGIAB is...', 'top_down')])).toEqual([
      { role: 'user', text: 'What is NGIAB?' },
      { role: 'assistant', text: 'NGIAB is...' },
    ]);
  });

  it('skips greetings, refusals, limit notices and errors with their questions', () => {
    const history = buildHistory([
      user('hi'),
      bot('Hi! I am...', 'help'),
      user('write an essay'),
      bot('I only answer CIROH questions', 'rejected'),
      user('What is TEEHR?'),
      bot('Sorry, I encountered an error'), // errors carry no route
      user('What is NGIAB?'),
      bot('NGIAB is...', 'bottom_up'),
    ]);
    expect(history.map(t => t.text)).toEqual(['What is NGIAB?', 'NGIAB is...']);
  });

  it('ignores an answer that is still streaming', () => {
    expect(buildHistory([user('q'), bot('partial', 'both', { isStreaming: true })])).toEqual([]);
  });

  it('keeps only the last three exchanges and trims long answers', () => {
    const messages: Message[] = [];
    for (let i = 0; i < 5; i++) messages.push(user(`q${i}`), bot(`a${i} ${'x'.repeat(3000)}`, 'both'));
    const history = buildHistory(messages);
    expect(history).toHaveLength(6);
    expect(history[0].text).toBe('q2');
    expect(history.every(t => t.text.length <= 2000)).toBe(true);
  });
});
