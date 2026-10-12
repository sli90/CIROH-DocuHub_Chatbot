// PrivacyNotice.tsx

import { Lock, Database, Eye, AlertTriangle } from 'lucide-react';
import { privacyPoints } from './data';

const ICONS = [Lock, Database, Eye, AlertTriangle];

export function PrivacyNotice({ isDarkMode }: { isDarkMode: boolean }) {
  return (
    <ul className="space-y-3">
      {privacyPoints.map((point, index) => {
        const Icon = ICONS[index % ICONS.length];
        return (
          <li key={point.title} className="flex gap-3">
            <div
              className={`mt-0.5 h-7 w-7 flex-shrink-0 rounded-full flex items-center justify-center ${
                isDarkMode ? 'bg-white/10 text-primary-300' : 'bg-primary-50 text-primary-600'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
            </div>
            <div>
              <p
                className={`text-sm font-semibold ${
                  isDarkMode ? 'text-gray-100' : 'text-gray-800'
                }`}
              >
                {point.title}
              </p>
              <p
                className={`text-xs leading-relaxed ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-600'
                }`}
              >
                {point.body}
              </p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
