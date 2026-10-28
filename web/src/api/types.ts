/**
 * TypeScript API Schema Definitions matching FastAPI Pydantic Models.
 * Strict type safety ensures zero fabrication or schema drift.
 */

export type RetrievalMode = 'baseline' | 'multi_context';
export type LLMProvider = 'auto' | 'local' | 'colab_remote';
export type EvidenceStatus = 'SUFFICIENT' | 'PARTIAL' | 'INSUFFICIENT';
export type DocumentCategory = 'product_manual' | 'troubleshooting' | 'warranty' | 'faq' | 'general';
export type DocumentLifecycleStatus = 
  | 'uploaded'
  | 'processed'
  | 'pending_index'
  | 'indexed'
  | 'indexing_failed'
  | 'deleted';

export interface Citation {
  document_source: string;
  page_or_section?: string | null;
  snippet: string;
  relevance_score: number;
  category?: string;
  chunk_id?: string | null;
  is_verified: boolean;
}

export interface QueryRequest {
  query: string;
  session_id?: string;
  user_id?: string;
  top_k?: number;
  retrieval_mode?: RetrievalMode;
  llm_provider?: LLMProvider;
}

export interface QueryResponse {
  query: string;
  expanded_query?: string | null;
  answer: string;
  retrieval_mode: RetrievalMode;
  selected_categories: string[];
  supporting_citations: Citation[];
  evidence_status: EvidenceStatus;
  retrieval_latency_ms: number;
  generation_latency_ms?: number | null;
  provider_status: string;
  evidence_found: boolean;
  citations: Citation[];
  retrieval_similarity?: number | null;
  confidence_score?: number | null;
  contexts_used: number;
  execution_time_ms: number;
  timing_breakdown?: Record<string, number>;
  citation_precision?: number | null;
  context_utilization?: number | null;
  requires_human_clarification: boolean;
  is_mock: boolean;
}

export interface DocumentSummary {
  document_id: string;
  filename: string;
  category: DocumentCategory;
  document_type: string;
  lifecycle_status: DocumentLifecycleStatus;
  is_searchable: boolean;
  chunk_count: number;
  file_size_bytes: number;
  version: number;
  first_ingested: string;
  last_seen: string;
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentSummary[];
}

export interface DocumentUploadResponse {
  status: string;
  document_id: string;
  filename: string;
  category: string;
  lifecycle_status: string;
  is_searchable: boolean;
  chunk_count: number;
  file_size_bytes: number;
  content_hash: string;
  message: string;
}

export interface DocumentDeleteResponse {
  status: string;
  message: string;
  document_id: string;
  deleted_chunks: number;
}

export interface KnowledgeBaseStatusResponse {
  status: string;
  total_active_documents: number;
  total_active_chunks: number;
  searchable_documents_count: number;
  documents_by_category: Record<string, number>;
  documents_by_lifecycle_status: Record<string, number>;
  vector_store: {
    collection_name: string | null;
    total_indexed_chunks: number;
    is_connected: boolean;
  };
  storage: {
    google_drive_connected: boolean;
    google_drive_root: string;
    local_free_disk_gb: number;
    storage_budget_mb: number;
  };
}

export interface FeedbackSubmission {
  query_id: string;
  rating: number; // 1 to 5
  correction?: string | null;
  flagged_incorrect: boolean;
  comment?: string | null;
}

export interface SystemHealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  uptime_seconds: number;
  storage: {
    google_drive_connected: boolean;
    google_drive_root: string;
    local_free_disk_gb: number;
    storage_budget_mb: number;
  };
  compute: {
    llm_provider: string;
    model_name: string;
  };
}

export interface SystemReadyResponse {
  status: 'ready' | 'not_ready';
  ready: boolean;
  checks: {
    storage: boolean;
    manifest: boolean;
    vector_store: boolean;
    embedding_provider: boolean;
    llm_provider: boolean;
  };
  details: {
    google_drive_connected: boolean;
    vector_store_collection: string | null;
    indexed_chunks_count: number;
    llm_provider: string;
    environment: string;
  };
}

export interface EvaluationSummaryResponse {
  status: string;
  development_benchmark: {
    title: string;
    model: string;
    total_queries: number;
    total_generations: number;
    aggregate_metrics: {
      baseline: {
        completed_generations: number;
        failed_generations: number;
        mean_answer_chars: number;
        mean_candidate_chunks: number;
        mean_asserted_citations: number;
        mean_approved_citations: number;
        unverified_hallucinated_citations: number;
        true_citation_precision: number;
        context_chunk_utilization: number;
        mean_retrieval_latency_ms: number;
        mean_generation_latency_ms: number;
        mean_total_latency_ms: number;
        p95_total_latency_ms: number;
      };
      multi_context: {
        completed_generations: number;
        failed_generations: number;
        mean_answer_chars: number;
        mean_candidate_chunks: number;
        mean_asserted_citations: number;
        mean_approved_citations: number;
        unverified_hallucinated_citations: number;
        true_citation_precision: number;
        context_chunk_utilization: number;
        mean_retrieval_latency_ms: number;
        mean_generation_latency_ms: number;
        mean_total_latency_ms: number;
        p95_total_latency_ms: number;
      };
    };
    metric_resolution_summary: {
      root_cause_of_41_25_pct: string;
      corrected_citation_precision: number;
      hallucination_rate: number;
      evidence_groundedness: string;
    };
    per_query_records: Array<{
      query_id: string;
      query: string;
      baseline: any;
      multi_context: any;
    }>;
  };
  held_out_benchmark: {
    title: string;
    model: string;
    total_queries: number;
    completed_queries: number;
    results: Array<{
      query_id: string;
      query: string;
      domain_category: string;
      ground_truth_claims: string[];
      baseline: any;
      multi_context: any;
    }>;
  };
  known_limitations: string[];
}
