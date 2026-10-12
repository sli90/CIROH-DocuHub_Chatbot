// ChatInput.tsx

import { Send } from 'lucide-react';
import { ChatInputProps } from './types';
import { DAILY_QUESTION_LIMIT } from './data';

export function ChatInput({
  inputValue,
  isBotResponding,
  onInputChange,
  onSendMessage,
  isDarkMode,
  email,
  quota,
  onShowPrivacy,
  onChangeEmail,
}: ChatInputProps) {
  const limitReached = quota !== null && quota.remaining === 0;
  const disabled = isBotResponding || limitReached;
  const muted = isDarkMode ? 'text-gray-400' : 'text-gray-500';
  const linkClass = `underline underline-offset-2 ${
    isDarkMode ? 'hover:text-gray-200' : 'hover:text-gray-700'
  }`;
  const quotaText = limitReached
    ? 'Daily limit reached. Resets at midnight US Central.'
    : quota?.remaining != null
      ? `${quota.remaining} of ${quota.limit} questions left today`
      : `${DAILY_QUESTION_LIMIT} questions per day`;

  return (
    // --- CHANGED: Differentiated background for input area ---
    <div
      className={`border-t p-4 ${
        isDarkMode ? 'border-gray-700 bg-gray-900' : 'border-gray-200 bg-white'
      }`}
    >
      <div className="flex items-center space-x-3">
        <input
          type="text"
          value={inputValue}
          onChange={e => onInputChange(e.target.value)}
          onKeyPress={e =>
            e.key === 'Enter' && !disabled && onSendMessage(inputValue)
          }
          placeholder={limitReached ? 'Daily question limit reached' : 'Type your message...'}
          className={`flex-1 px-4 py-2 border rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-shadow ${
            isDarkMode
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'border-gray-300 bg-white' // Keep input solid for readability
          }`}
          disabled={disabled}
          aria-label="Your question"
        />
        <button
          onClick={() => onSendMessage(inputValue)}
          disabled={!inputValue.trim() || disabled}
          className="group flex-shrink-0 w-10 h-10 bg-primary-600 text-white rounded-full hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center"
          title="Send message"
        >
          <Send className="h-5 w-5 transition-transform duration-200 group-hover:translate-x-0.5" />
        </button>
      </div>
      <div className={`mt-2 flex flex-wrap items-center justify-center gap-x-1.5 text-[11px] ${muted}`}>
        <span className={limitReached ? 'text-amber-500' : ''}>{quotaText}</span>
        <span aria-hidden="true">·</span>
        <button type="button" onClick={onShowPrivacy} className={linkClass}>
          Privacy
        </button>
        <span aria-hidden="true">·</span>
        <span className="truncate max-w-[12rem]" title={email}>
          {email}
        </span>
        <button type="button" onClick={onChangeEmail} className={linkClass}>
          Change
        </button>
      </div>
    </div>
  );
}