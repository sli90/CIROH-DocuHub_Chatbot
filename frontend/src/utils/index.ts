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
  
  // Skip if text already contains HTML tags (already processed)
  if (text.includes('<') && text.includes('>')) {
    return text;
  }
  
  // Skip if text contains any HTML attributes (already processed)
  if (text.includes('class=') || text.includes('href=') || text.includes('target=') || 
      text.includes('rel=') || text.includes('mailto:')) {
    return text;
  }
  
  // Skip if text contains HTML fragments (already processed)
  if (text.includes('" class=') || text.includes('">') || text.includes('</a>') ||
      text.includes('target="_blank"') || text.includes('rel="noopener noreferrer"')) {
    return text;
  }
  
  let formattedText = text;
  
  // First, convert email addresses to clickable mailto links
  const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g;
  formattedText = formattedText.replace(emailRegex, (email) => {
    return `<a href="mailto:${email}" class="text-blue-400 hover:text-blue-300 underline">${email}</a>`;
  });
  
  // Then, convert https:// URLs to clickable links
  const httpsUrlRegex = /(https?:\/\/[^\s<>]+)/g;
  formattedText = formattedText.replace(httpsUrlRegex, (url) => {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline">${url}</a>`;
  });
  
  
  return formattedText;
}