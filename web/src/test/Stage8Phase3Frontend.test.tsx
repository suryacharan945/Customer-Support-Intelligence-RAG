import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatMessage } from '../components/chat/ChatMessage';
import { CitationCard } from '../components/chat/CitationCard';
import { CategoryBadge, EvidenceBadge } from '../components/common/Badge';
import { UploadDropzone } from '../components/documents/UploadDropzone';
import { QueryResponse, Citation } from '../api/types';

describe('Stage 8 Phase 3 Generalized Document Intelligence Frontend Suite', () => {
  const sampleDossierCitation: Citation = {
    document_source: 'AI Customer Support Intelligence Platform - Project Dossier.pdf',
    page_or_section: 'Page 3',
    snippet: 'The platform integrates dense semantic embeddings with BM25 lexical retrieval using Reciprocal Rank Fusion (RRF).',
    relevance_score: 0.96,
    category: 'architecture',
    chunk_id: 'dossier_chunk_03',
    is_verified: true,
  };

  const samplePrinterCitation: Citation = {
    document_source: 'prox400_troubleshooting.md',
    page_or_section: 'Section 4.1',
    snippet: 'For Error E-101 (Printhead Carriage Jam), power cycle the printer: switch off, unplug for 60 seconds.',
    relevance_score: 0.92,
    category: 'troubleshooting',
    chunk_id: 'printer_chunk_12',
    is_verified: true,
  };

  const buildMockResponse = (overrides: Partial<QueryResponse>): QueryResponse => ({
    query: 'Default test query',
    answer: 'Default test answer',
    retrieval_mode: 'multi_context',
    selected_categories: ['general'],
    supporting_citations: [],
    evidence_status: 'SUFFICIENT',
    retrieval_latency_ms: 540.2,
    generation_latency_ms: 18.5,
    provider_status: 'LOCAL_GROUNDED_SYNTHESIS',
    evidence_found: true,
    citations: [],
    contexts_used: 3,
    execution_time_ms: 558.7,
    requires_human_clarification: false,
    is_mock: false,
    ...overrides,
  });

  it('1. renders general document question with adaptive headings and structured sections', () => {
    const mockResponse = buildMockResponse({
      query: 'Explain the platform architecture',
      answer: '### System Architecture\nThe architecture employs a dual-stage retrieval engine.\n\n### Technology Stack\n- FastAPI\n- ChromaDB\n- React 18',
      supporting_citations: [sampleDossierCitation],
      citations: [sampleDossierCitation],
      retrieval_latency_ms: 540.2,
      generation_latency_ms: 18.5,
    });

    render(
      <ChatMessage
        query={mockResponse.query}
        response={mockResponse}
        turnId="turn_1"
      />
    );

    // Verify adaptive heading renders
    expect(screen.getByText(/System Architecture/i)).toBeInTheDocument();
    expect(screen.getByText(/Technology Stack/i)).toBeInTheDocument();
    // Verify content text
    expect(screen.getByText(/dual-stage retrieval engine/i)).toBeInTheDocument();
    // Verify citation rendering
    expect(screen.getByText(/AI Customer Support Intelligence Platform - Project Dossier.pdf/i)).toBeInTheDocument();
    // Verify separate retrieval and local synthesis latency badges
    expect(screen.getByText(/Ret: 540.2ms/i)).toBeInTheDocument();
    expect(screen.getByText(/Local Syn: 18.5ms/i)).toBeInTheDocument();
  });

  it('2. renders printer customer support question preserving troubleshooting workflow', () => {
    const mockResponse = buildMockResponse({
      query: 'How to fix error E-101?',
      answer: '### Resolution Steps\n1. Turn off printer.\n2. Disconnect power cord for 60 seconds.\n3. Reconnect and inspect carriage path.',
      supporting_citations: [samplePrinterCitation],
      citations: [samplePrinterCitation],
      evidence_status: 'SUFFICIENT',
      retrieval_latency_ms: 320.0,
      generation_latency_ms: 15.2,
    });

    render(
      <ChatMessage
        query={mockResponse.query}
        response={mockResponse}
        turnId="turn_2"
      />
    );

    expect(screen.getByText(/Resolution Steps/i)).toBeInTheDocument();
    expect(screen.getByText(/Turn off printer/i)).toBeInTheDocument();
    expect(screen.getByText(/prox400_troubleshooting.md/i)).toBeInTheDocument();
    expect(screen.getByText(/Sufficient Grounding/i)).toBeInTheDocument();
  });

  it('3. renders GitHub-Flavored Markdown tables accurately for benchmark comparisons', () => {
    const mockResponse = buildMockResponse({
      query: 'What are the benchmark results?',
      answer: `### Benchmark Results
| Metric | Baseline RAG | Multi-Context RAG | Delta |
| :--- | :--- | :--- | :--- |
| Precision@3 | 64.2% | 91.8% | +27.6% |
| Recall | 58.0% | 88.4% | +30.4% |`,
      evidence_status: 'SUFFICIENT',
    });

    render(
      <ChatMessage
        query={mockResponse.query}
        response={mockResponse}
        turnId="turn_3"
      />
    );

    // Verify table elements
    expect(screen.getByText('Metric')).toBeInTheDocument();
    expect(screen.getByText('Baseline RAG')).toBeInTheDocument();
    expect(screen.getByText('Multi-Context RAG')).toBeInTheDocument();
    expect(screen.getByText('Precision@3')).toBeInTheDocument();
    expect(screen.getByText('+27.6%')).toBeInTheDocument();
    expect(screen.getByText('Recall')).toBeInTheDocument();
  });

  it('4. renders dynamic citations with file format icon, chunk ID, relevance, and location', () => {
    render(
      <CitationCard
        supportingCitations={[sampleDossierCitation]}
        candidateCitations={[sampleDossierCitation]}
      />
    );

    expect(screen.getByText(/AI Customer Support Intelligence Platform - Project Dossier.pdf/i)).toBeInTheDocument();
    expect(screen.getByText(/Location: Page 3/i)).toBeInTheDocument();
    expect(screen.getByText(/Score: 96%/i)).toBeInTheDocument();
    expect(screen.getByText(/chunk: dossier_chunk_03/i)).toBeInTheDocument();
    expect(screen.getByText('📄 PDF')).toBeInTheDocument();
  });

  it('5. opens EvidenceDrawer when inspect button is clicked and displays verbatim excerpt and copy button', async () => {
    render(
      <CitationCard
        supportingCitations={[sampleDossierCitation]}
        candidateCitations={[sampleDossierCitation]}
        queryContext="Explain the platform retrieval architecture"
      />
    );

    // Click to open evidence drawer via the inspect button
    const inspectBtn = screen.getByRole('button', { name: /inspect evidence/i });
    fireEvent.click(inspectBtn);

    // Verify EvidenceDrawer opens with metadata and verbatim content
    expect(screen.getByText(/Verified Evidence Excerpt/i)).toBeInTheDocument();
    expect(screen.getByText(/Grounding Query Context/i)).toBeInTheDocument();
    expect(screen.getByText(/"Explain the platform retrieval architecture"/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Reciprocal Rank Fusion \(RRF\)/i).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/Citation ID Validity Verified/i)).toBeInTheDocument();

    // Verify Drawer Copy button
    const copyBtn = screen.getByRole('button', { name: /copy excerpt/i });
    expect(copyBtn).toBeInTheDocument();

    // Click close button
    const closeBtn = screen.getByRole('button', { name: /close evidence drawer/i });
    fireEvent.click(closeBtn);

    await waitFor(() => {
      expect(screen.queryByText(/Verified Evidence Excerpt/i)).not.toBeInTheDocument();
    });
  });

  it('6. renders insufficient evidence honest abstention banner when grounding is lacking', () => {
    const mockResponse = buildMockResponse({
      query: 'What is the recipe for chicken biryani?',
      answer: 'I could not find relevant information in the indexed knowledge base to answer this question.',
      evidence_status: 'INSUFFICIENT',
      supporting_citations: [],
      citations: [],
      evidence_found: false,
    });

    render(
      <ChatMessage
        query={mockResponse.query}
        response={mockResponse}
        turnId="turn_6"
      />
    );

    expect(screen.getByText(/Honest Abstention:/i)).toBeInTheDocument();
    expect(screen.getByText(/The requested information was not found in the indexed knowledge base/i)).toBeInTheDocument();
    expect(screen.getByText(/Insufficient Evidence/i)).toBeInTheDocument();
  });

  it('7. renders all new DocumentCategory badges including engineering, architecture, evaluation, and general', () => {
    render(
      <div>
        <CategoryBadge category="engineering" />
        <CategoryBadge category="architecture" />
        <CategoryBadge category="evaluation" />
        <CategoryBadge category="general" />
      </div>
    );

    expect(screen.getByText(/Engineering/i)).toBeInTheDocument();
    expect(screen.getByText(/Architecture/i)).toBeInTheDocument();
    expect(screen.getByText(/Evaluation & Benchmarks/i)).toBeInTheDocument();
    expect(screen.getByText(/General Document/i)).toBeInTheDocument();
  });

  it('8. provides expanded categories in UploadDropzone', () => {
    render(<UploadDropzone onSuccess={vi.fn()} />);

    expect(screen.getByText(/engineering \(Architecture, Code & Engineering\)/i)).toBeInTheDocument();
    expect(screen.getByText(/architecture \(System Architecture & Designs\)/i)).toBeInTheDocument();
    expect(screen.getByText(/evaluation \(Benchmarks, Metrics & Audits\)/i)).toBeInTheDocument();
    expect(screen.getByText(/general \(Reports, Research & General Knowledge\)/i)).toBeInTheDocument();
  });
});
