import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';
import { LifecycleBadge, CategoryBadge, EvidenceBadge, ProviderBadge } from '../components/common/Badge';

// Mock API responses for testing
vi.mock('../api/client', () => ({
  apiClient: {
    getHealth: vi.fn().mockResolvedValue({
      status: 'healthy',
      app_name: 'ApexPrint Multi-Context RAG',
      version: '1.0.0',
      uptime_seconds: 120,
      storage: { google_drive_connected: true, local_free_disk_gb: 15.2, storage_budget_mb: 1024 },
      compute: { llm_provider: 'auto', model_name: 'Mistral-7B' },
    }),
    getKnowledgeBaseStatus: vi.fn().mockResolvedValue({
      status: 'operational',
      total_active_documents: 9,
      total_active_chunks: 32,
      searchable_documents_count: 9,
      documents_by_category: { product_manual: 3, troubleshooting: 2, warranty: 2, faq: 2 },
      documents_by_lifecycle_status: { indexed: 9 },
      vector_store: { collection_name: 'apexprint_knowledge_base', total_indexed_chunks: 32, is_connected: true },
      storage: { google_drive_connected: true, google_drive_root: 'G:\\My Drive', local_free_disk_gb: 15.2, storage_budget_mb: 1024 },
    }),
    listDocuments: vi.fn().mockResolvedValue({
      total: 1,
      documents: [
        {
          document_id: 'doc_test_001',
          filename: 'apexprint_prox400_user_manual.md',
          category: 'product_manual',
          document_type: 'md',
          lifecycle_status: 'indexed',
          is_searchable: true,
          chunk_count: 5,
          file_size_bytes: 2048,
          version: 1,
          first_ingested: '2026-10-28T10:00:00Z',
          last_seen: '2026-10-28T10:00:00Z',
        },
      ],
    }),
    getReady: vi.fn().mockResolvedValue({
      status: 'ready',
      ready: true,
      checks: { storage: true, manifest: true, vector_store: true, embedding_provider: true, llm_provider: true },
      details: { google_drive_connected: true, vector_store_collection: 'test', indexed_chunks_count: 32, llm_provider: 'auto', environment: 'development' },
    }),
    getEvaluationSummary: vi.fn().mockResolvedValue({
      status: 'success',
      development_benchmark: {
        title: 'Stage 8 Comparative Evaluation',
        model: 'mistralai/Mistral-7B-Instruct-v0.3',
        total_queries: 16,
        total_generations: 32,
        aggregate_metrics: {
          baseline: { mean_retrieval_latency_ms: 0.17, mean_generation_latency_ms: 12386, p95_total_latency_ms: 17399 },
          multi_context: { mean_retrieval_latency_ms: 0.63, mean_generation_latency_ms: 26518, p95_total_latency_ms: 29159 },
        },
        metric_resolution_summary: { root_cause_of_41_25_pct: 'context utilization vs precision' },
        per_query_records: [],
      },
      held_out_benchmark: { total_queries: 10, completed_queries: 10, results: [] },
      known_limitations: ['Synthetic enterprise printer documentation.'],
    }),
  },
}));

describe('ApexPrint Web Application Test Suite', () => {
  it('renders Dashboard with brand heading and navigation', async () => {
    render(<App />);
    expect(screen.getByText(/ApexPrint AI/i)).toBeInTheDocument();
    expect(screen.getByText(/RAG \+ MCP Capstone/i)).toBeInTheDocument();
    expect(screen.getByText(/System Overview/i)).toBeInTheDocument();
  });

  it('renders status badges with accurate labels and styles', () => {
    render(
      <div>
        <LifecycleBadge status="indexed" isSearchable={true} />
        <LifecycleBadge status="pending_index" isSearchable={false} />
        <CategoryBadge category="troubleshooting" />
        <CategoryBadge category="warranty" />
        <EvidenceBadge status="SUFFICIENT" />
        <ProviderBadge status="LOCAL_GROUNDED_SYNTHESIS" />
        <ProviderBadge status="LOCAL_GROUNDED_FALLBACK" />
      </div>
    );

    expect(screen.getByText(/Indexed & Searchable/i)).toBeInTheDocument();
    expect(screen.getByText(/Pending Indexing/i)).toBeInTheDocument();
    expect(screen.getByText(/Troubleshooting/i)).toBeInTheDocument();
    expect(screen.getByText(/Warranty & SLA/i)).toBeInTheDocument();
    expect(screen.getByText(/Sufficient Grounding/i)).toBeInTheDocument();
    expect(screen.getByText(/Local Grounded Engine/i)).toBeInTheDocument();
    expect(screen.getByText(/Local Grounded Fallback/i)).toBeInTheDocument();
  });
});
