import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ModeSelector } from '../components/chat/ModeSelector';
import { CitationCard } from '../components/chat/CitationCard';
import { ChatProvider } from '../context/ChatContext';

describe('Chat Components & Controls Test Suite', () => {
  it('renders ModeSelector and switches RAG modes', () => {
    render(
      <ChatProvider>
        <ModeSelector />
      </ChatProvider>
    );

    const multiBtn = screen.getByRole('button', { name: /multi-context/i });
    const baseBtn = screen.getByRole('button', { name: /baseline/i });

    expect(multiBtn).toBeInTheDocument();
    expect(baseBtn).toBeInTheDocument();

    // Toggle baseline
    fireEvent.click(baseBtn);
    expect(screen.getByText(/Baseline Dense/i)).toBeInTheDocument();

    // Toggle back to multi-context
    fireEvent.click(multiBtn);
    expect(screen.getByText(/MCP Hybrid \(Dense \+ BM25\)/i)).toBeInTheDocument();
  });

  it('renders CitationCard with verified badges and expands details', () => {
    const mockCitations = [
      {
        document_source: 'prox400_troubleshooting.pdf',
        page_or_section: 'Page 4',
        snippet: 'For Error E-101, power cycle the printer: switch off, unplug for 60 seconds.',
        relevance_score: 0.94,
        category: 'troubleshooting',
        chunk_id: 'chunk_t2',
        is_verified: true,
      },
    ];

    render(
      <CitationCard
        supportingCitations={mockCitations}
        candidateCitations={mockCitations}
      />
    );

    expect(screen.getByText(/Verified Supporting Evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/prox400_troubleshooting.pdf/i)).toBeInTheDocument();
    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText(/Location: Page 4/i)).toBeInTheDocument();
    expect(screen.getByText(/Score: 94%/i)).toBeInTheDocument();
  });
});
