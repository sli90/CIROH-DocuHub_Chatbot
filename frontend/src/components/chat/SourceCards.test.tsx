import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SourceCards, sourcesForMessage } from './SourceCards';
import { normalizeEmail } from '../../services/user';
import type { Message } from './types';

const baseMessage: Message = { id: '1', text: 'answer', isBot: true, timestamp: new Date() };

describe('sourcesForMessage', () => {
  it('prefers structured source details', () => {
    const details = [{ title: 'Install guide', path: 'Products > NGIAB', url: '/docs/x' }];
    expect(sourcesForMessage({ ...baseMessage, sourceDetails: details })).toEqual(details);
  });

  it('rebuilds cards from breadcrumb strings for older messages', () => {
    const cards = sourcesForMessage({
      ...baseMessage,
      sources: 'CIROH Hub > Products > NGIAB\nA paper',
      links: '/docs/products/ngiab\nhttps://doi.org/x',
    });
    expect(cards).toEqual([
      { title: 'NGIAB', path: 'CIROH Hub > Products', url: '/docs/products/ngiab' },
      { title: 'A paper', path: '', url: 'https://doi.org/x' },
    ]);
  });
});

describe('SourceCards', () => {
  it('renders one link card per source, with relative links made absolute', () => {
    render(
      <SourceCards
        isDarkMode={false}
        sources={[
          { title: 'Install guide', path: 'Products > NGIAB', url: '/docs/products/ngiab', type: 'Hub Page' },
          { title: 'A paper', url: 'https://doi.org/10.1/x', type: 'Publication' },
        ]}
      />
    );
    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(2);
    expect(links[0].getAttribute('href')).toBe('https://docs.ciroh.org/docs/products/ngiab');
    expect(links[1].getAttribute('target')).toBe('_blank');
    expect(screen.getByText('Sources (2)')).toBeTruthy();
  });

  it('renders nothing without sources', () => {
    const { container } = render(<SourceCards isDarkMode={false} sources={[]} />);
    expect(container.innerHTML).toBe('');
  });
});

describe('normalizeEmail', () => {
  it('trims and lower-cases valid addresses', () => {
    expect(normalizeEmail('  Jane.Doe@UA.edu ')).toBe('jane.doe@ua.edu');
  });

  it('rejects invalid addresses', () => {
    for (const bad of ['', 'nope', 'a@b', 'a b@ua.edu', '@ua.edu', 'x@ua.e']) {
      expect(normalizeEmail(bad)).toBeNull();
    }
  });
});
