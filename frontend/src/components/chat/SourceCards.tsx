// SourceCards.tsx
//
// The documents behind an answer, as a horizontally scrollable row of cards
// (short title, the section it lives in, and the site) instead of a list of
// long breadcrumb links.

import { BookOpen, Database, ExternalLink, FileText, Github } from 'lucide-react';
import type { Message, SourceDetail } from './types';

const DOCS_ORIGIN = 'https://docs.ciroh.org';

function absoluteUrl(url?: string): string | undefined {
  if (!url) return undefined;
  const trimmed = url.trim();
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  return `${DOCS_ORIGIN}${trimmed.startsWith('/') ? '' : '/'}${trimmed}`;
}

function hostname(url?: string): string {
  if (!url) return '';
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
}

function iconFor(source: SourceDetail, url?: string) {
  const hint = `${source.type ?? ''} ${url ?? ''}`.toLowerCase();
  if (hint.includes('github') || hint.includes('repo') || hint.includes('code')) return Github;
  if (hint.includes('dataset') || hint.includes('hydroshare') || hint.includes('data')) return Database;
  if (hint.includes('publication') || hint.includes('paper') || hint.includes('doi.org')) return BookOpen;
  return FileText;
}

/** Cards for a message: structured details when the API sent them,
 * otherwise rebuilt from the older "A > B > C" breadcrumb strings. */
export function sourcesForMessage(message: Message): SourceDetail[] {
  if (message.sourceDetails?.length) return message.sourceDetails;
  const toList = (value?: string | string[]) =>
    !value ? [] : Array.isArray(value) ? value : value.split('\n').filter(line => line.trim());
  const links = toList(message.links);
  return toList(message.sources).map((breadcrumb, index) => {
    const parts = breadcrumb.split(' > ').map(part => part.trim()).filter(Boolean);
    const linkParts = (links[index] ?? '').split(' > ').map(part => part.trim()).filter(Boolean);
    return {
      title: parts[parts.length - 1] ?? breadcrumb,
      path: parts.slice(0, -1).join(' > '),
      url: linkParts[linkParts.length - 1],
    };
  });
}

interface SourceCardsProps {
  sources: SourceDetail[];
  isDarkMode: boolean;
}

export function SourceCards({ sources, isDarkMode }: SourceCardsProps) {
  if (!sources.length) return null;

  return (
    <div className="mt-3">
      <div
        className={`flex items-center justify-between text-xs font-medium mb-1.5 ${
          isDarkMode ? 'text-gray-300' : 'text-gray-600'
        }`}
      >
        <span>Sources ({sources.length})</span>
        {sources.length > 1 && (
          <span className={isDarkMode ? 'text-gray-500' : 'text-gray-400'}>Scroll for more →</span>
        )}
      </div>
      <ul
        className="source-cards flex gap-2 overflow-x-auto snap-x snap-mandatory pb-2 -mx-1 px-1"
        aria-label="Sources"
      >
        {sources.map((source, index) => {
          const url = absoluteUrl(source.url);
          const Icon = iconFor(source, url);
          const site = hostname(url);
          const body = (
            <>
              <div className="flex items-center gap-1.5 mb-1">
                <span
                  className={`h-5 w-5 rounded-md flex items-center justify-center flex-shrink-0 ${
                    isDarkMode ? 'bg-white/10 text-primary-300' : 'bg-primary-50 text-primary-600'
                  }`}
                >
                  <Icon className="h-3 w-3" />
                </span>
                <span
                  className={`text-[11px] truncate ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}
                >
                  {source.type || site || `Source ${index + 1}`}
                </span>
                {url && (
                  <ExternalLink
                    className={`h-3 w-3 ml-auto flex-shrink-0 ${
                      isDarkMode ? 'text-gray-500' : 'text-gray-400'
                    }`}
                  />
                )}
              </div>
              <p
                className={`text-xs font-semibold leading-snug line-clamp-2 ${
                  isDarkMode ? 'text-gray-100' : 'text-gray-800'
                }`}
                title={source.title}
              >
                {source.title}
              </p>
              {source.path && (
                <p
                  className={`text-[11px] mt-1 truncate ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}
                  title={source.path}
                >
                  {source.path}
                </p>
              )}
            </>
          );
          const cardClass = `block h-full w-44 rounded-lg border p-2.5 transition-colors ${
            isDarkMode
              ? 'border-white/10 bg-gray-800 hover:bg-gray-700/80'
              : 'border-gray-200 bg-white hover:border-primary-300 hover:bg-primary-50/40'
          }`;
          return (
            <li key={`${index}-${source.title}`} className="snap-start flex-shrink-0">
              {url ? (
                <a href={url} target="_blank" rel="noopener noreferrer" className={cardClass}>
                  {body}
                </a>
              ) : (
                <div className={cardClass}>{body}</div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
