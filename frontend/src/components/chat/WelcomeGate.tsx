// WelcomeGate.tsx
//
// First screen of the chat: the privacy notice plus the email the visitor
// must provide before asking questions (the API limits questions per email
// per day).

import { FormEvent, useState } from 'react';
import { Bot, ArrowRight } from 'lucide-react';
import { PrivacyNotice } from './PrivacyNotice';
import { DAILY_QUESTION_LIMIT } from './data';
import { normalizeEmail } from '../../services/user';

interface WelcomeGateProps {
  isDarkMode: boolean;
  initialEmail?: string | null;
  onSubmit: (email: string) => void;
}

export function WelcomeGate({ isDarkMode, initialEmail, onSubmit }: WelcomeGateProps) {
  const [value, setValue] = useState(initialEmail ?? '');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const email = normalizeEmail(value);
    if (!email) {
      setError('Please enter a valid email address.');
      return;
    }
    onSubmit(email);
  };

  const muted = isDarkMode ? 'text-gray-400' : 'text-gray-500';

  return (
    <div className="space-y-5">
      <div className="text-center space-y-2 pt-1">
        <div
          className={`mx-auto h-11 w-11 rounded-full flex items-center justify-center ${
            isDarkMode ? 'bg-gray-700' : 'bg-primary-500/15'
          }`}
        >
          <Bot className={`h-6 w-6 ${isDarkMode ? 'text-gray-200' : 'text-primary-600'}`} />
        </div>
        <h2 className={`text-base font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
          Welcome to CIROH AI
        </h2>
        <p className={`text-sm ${muted}`}>
          Ask about CIROH tools, data, services and research. Answers come from
          CIROH documentation, with sources.
        </p>
      </div>

      <section
        className={`rounded-xl border p-4 ${
          isDarkMode ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'
        }`}
        aria-labelledby="privacy-heading"
      >
        <h3
          id="privacy-heading"
          className={`text-xs font-semibold uppercase tracking-wide mb-3 ${muted}`}
        >
          Your privacy
        </h3>
        <PrivacyNotice isDarkMode={isDarkMode} />
      </section>

      <form onSubmit={handleSubmit} className="space-y-2" noValidate>
        <label
          htmlFor="ciroh-chat-email"
          className={`block text-sm font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}
        >
          Your email address
        </label>
        <input
          id="ciroh-chat-email"
          type="email"
          autoComplete="email"
          value={value}
          onChange={e => {
            setValue(e.target.value);
            setError(null);
          }}
          placeholder="name@university.edu"
          aria-invalid={error ? true : undefined}
          aria-describedby="ciroh-chat-email-help"
          className={`w-full px-4 py-2 border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            isDarkMode
              ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
              : 'bg-white border-gray-300'
          }`}
        />
        <p
          id="ciroh-chat-email-help"
          className={`text-xs ${error ? 'text-red-500' : muted}`}
          role={error ? 'alert' : undefined}
        >
          {error ?? `Used only to apply the limit of ${DAILY_QUESTION_LIMIT} questions per day.`}
        </p>
        <button
          type="submit"
          className="w-full mt-1 flex items-center justify-center gap-2 rounded-full bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium py-2.5 transition-colors"
        >
          Agree and start chatting
          <ArrowRight className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
