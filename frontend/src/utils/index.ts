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
          // Use the link part directly as the URL path (no need to join with /)
          const fullUrl = `https://docs.ciroh.org${linkPart}`;
          return `<a href="${fullUrl}" target="_blank" rel="noopener noreferrer" class="text-gray-400 hover:text-gray-300 underline">${part}</a>`;
        }
        return part;
      });
      
      return clickableParts.join(' > ');
    }
    return source;
  }).join('\n');
}

export function formatUrlsAsHtml(text: string): string {
  if (!text) return '';
  
  // Convert markdown-style links [text](url) to HTML links
  const markdownLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  
  return text.replace(markdownLinkRegex, (_, linkText, url) => {
    // Ensure URL has protocol
    const fullUrl = url.startsWith('http') ? url : `https://${url}`;
    return `<a href="${fullUrl}" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline">${linkText}</a>`;
  });
}