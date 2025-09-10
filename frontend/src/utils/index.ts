import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(date));
}

export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}

export function formatUrls(text: string): string {
  // URL regex pattern
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  
  return text.replace(urlRegex, (url) => {
    // Don't add line breaks to URLs - let CSS handle the wrapping
    return url;
  });
}

export function formatUrlsAsHtml(text: string): string {
  // Process both Markdown links and plain URLs in a single pass
  // This regex matches either [text](url) or plain URLs
  const combinedRegex = /(\[([^\]]+)\]\(([^)]+)\)|(https?:\/\/[^\s<>"']+))/g;
  
  return text.replace(combinedRegex, (match, fullMatch, linkText, markdownUrl, plainUrl) => {
    // If it's a Markdown link [text](url)
    if (linkText && markdownUrl) {
      return `<a href="${markdownUrl}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">${linkText}</a>`;
    }
    // If it's a plain URL
    else if (plainUrl) {
      return `<a href="${plainUrl}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">${plainUrl}</a>`;
    }
    return match;
  });
}

export function formatSources(sources: string): string {
  // Split by newlines and format each source
  return sources
    .split('\n')
    .map(source => {
      source = source.trim();
      if (!source) return '';
      
      // If it looks like a URL, format it
      if (source.startsWith('http')) {
        return formatUrls(source);
      }
      
      return source;
    })
    .filter(source => source.length > 0)
    .join('\n');
}

export function formatSourcesAsHtml(sources: string): string {
  // Split by newlines and format each source as HTML
  return sources
    .split('\n')
    .map(source => {
      source = source.trim();
      if (!source) return '';
      
      // If it looks like a URL, create a clickable link
      if (source.startsWith('http')) {
        // Don't truncate URLs - let CSS handle the wrapping
        return `<a href="${source}" target="_blank" rel="noopener noreferrer" class="source-link">${source}</a>`;
      }
      
      return source;
    })
    .filter(source => source.length > 0)
    .join('<br>');
}