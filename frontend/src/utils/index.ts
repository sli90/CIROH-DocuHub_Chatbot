// Utility functions for formatting sources and links

export function formatSourcesAsHtml(sources: string | string[], links?: string | string[]): string {
  if (!sources) return '';
  
  // Convert to array if it's a string
  const sourceLines = Array.isArray(sources) ? sources : sources.split('\n').filter(line => line.trim());
  const linkLines = links ? (Array.isArray(links) ? links : links.split('\n').filter(line => line.trim())) : [];
  
  return sourceLines.map((source, index) => {
    const link = linkLines[index];
    if (link) {
      // Split both source and link by > to create individual clickable parts
      const sourceParts = source.split(' > ').map(part => part.trim());
      const linkParts = link.split(' > ').map(part => part.trim());
      
      // Create individual links for each part
      const clickableParts = sourceParts.map((part, partIndex) => {
        const linkPart = linkParts[partIndex];
        if (linkPart) {
          // Check if linkPart already contains a full URL (starts with http:// or https://)
          const fullUrl = linkPart.startsWith('http://') || linkPart.startsWith('https://') 
            ? linkPart 
            : `https://docs.ciroh.org${linkPart}`;
          return `<a href="${fullUrl}" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-gray-300 underline">${part}</a>`;
        }
        return part;
      });
      
      return clickableParts.join(' > ');
    }
    return source;
  }).join('\n');
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function withPlaceholders(html: string, pattern: RegExp): { html: string; slots: string[] } {
  const slots: string[] = [];
  const replaced = html.replace(pattern, match => {
    slots.push(match);
    return `\u0000${slots.length - 1}\u0000`;
  });
  return { html: replaced, slots };
}

function restorePlaceholders(html: string, slots: string[]): string {
  return html.replace(/\u0000(\d+)\u0000/g, (_, index) => slots[Number(index)] ?? '');
}

export function formatUrlsAsHtml(text: string): string {
  if (!text) return '';

  let formattedText = escapeHtml(text);

  // Markdown that the RAG model commonly emits
  formattedText = formattedText.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  formattedText = formattedText.replace(/__(.+?)__/g, '<strong>$1</strong>');
  formattedText = formattedText.replace(
    /(^|[^\*])\*([^*\n]+)\*(?!\*)/g,
    '$1<em>$2</em>'
  );
  formattedText = formattedText.replace(/`([^`]+)`/g, '<code>$1</code>');
  formattedText = formattedText.replace(
    /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline">$1</a>'
  );

  const saved = withPlaceholders(formattedText, /<a\b[^>]*>.*?<\/a>/gi);
  formattedText = saved.html;

  formattedText = formattedText.replace(
    /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g,
    email =>
      `<a href="mailto:${email}" class="text-blue-400 hover:text-blue-300 underline">${email}</a>`
  );

  formattedText = formattedText.replace(
    /(https?:\/\/[^\s<>]+)/g,
    url =>
      `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline">${url}</a>`
  );

  return restorePlaceholders(formattedText, saved.slots);
}