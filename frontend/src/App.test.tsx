import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the chat bubble', () => {
    render(<App />);

    // Check if the iframe is rendered
    const iframe = screen.getByTitle('CIROH DocuHub Background');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'https://docs.ciroh.org/');
  });

  it('renders without crashing', () => {
    expect(() => render(<App />)).not.toThrow();
  });
});
