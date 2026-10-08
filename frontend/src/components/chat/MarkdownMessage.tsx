// MarkdownMessage.tsx

import ReactMarkdown, { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownMessageProps {
  text: string;
  isDarkMode: boolean;
}

// Bot replies are Markdown (headings, lists, tables, code). react-markdown
// renders to React elements and ignores raw HTML, so this is XSS-safe
// without dangerouslySetInnerHTML.
export function MarkdownMessage({ text, isDarkMode }: MarkdownMessageProps) {
  const linkClass = isDarkMode
    ? 'text-blue-300 hover:text-blue-200 underline'
    : 'text-blue-600 hover:text-blue-700 underline';

  const components: Components = {
    a: ({ href, children }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={linkClass}
      >
        {children}
      </a>
    ),
    table: ({ children }) => (
      <div className="overflow-x-auto">
        <table>{children}</table>
      </div>
    ),
  };

  return (
    <div className={`chat-markdown ${isDarkMode ? 'chat-markdown-dark' : ''}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {text}
      </ReactMarkdown>
    </div>
  );
}
