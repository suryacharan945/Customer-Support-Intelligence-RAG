/**
 * Centralized API Client for ApexPrint Customer Support Platform.
 * Communicates with FastAPI backend with structured error handling,
 * request timeouts, and zero client-side credential exposure.
 */

import {
  QueryRequest,
  QueryResponse,
  DocumentListResponse,
  DocumentSummary,
  DocumentUploadResponse,
  DocumentDeleteResponse,
  KnowledgeBaseStatusResponse,
  FeedbackSubmission,
  SystemHealthResponse,
  SystemReadyResponse,
  EvaluationSummaryResponse,
} from './types';

export class ApiClientError extends Error {
  public status: number;
  public details: any;

  constructor(message: string, status: number = 500, details: any = null) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.details = details;
  }
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    // Defaults to relative /api/v1 (proxied by Vite in dev, or direct FastAPI in production)
    const envUrl = import.meta.env.VITE_API_BASE_URL;
    this.baseUrl = envUrl ? envUrl.replace(/\/+$/, '') : '/api/v1';
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs: number = 30000
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timer);

      if (!response.ok) {
        let errorData: any = {};
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText || `HTTP ${response.status}` };
        }

        const message = 
          typeof errorData.detail === 'string'
            ? errorData.detail
            : Array.isArray(errorData.detail)
            ? errorData.detail.map((e: any) => `${e.loc?.join('.') || 'param'}: ${e.msg}`).join(', ')
            : `API Error: ${response.status} ${response.statusText}`;

        throw new ApiClientError(message, response.status, errorData);
      }

      return await response.json();
    } catch (err: any) {
      clearTimeout(timer);
      if (err.name === 'AbortError') {
        throw new ApiClientError(`Request to '${endpoint}' timed out after ${timeoutMs / 1000}s`, 408);
      }
      if (err instanceof ApiClientError) {
        throw err;
      }
      throw new ApiClientError(`Network connection error: ${err.message || 'FastAPI backend unreachable'}`, 503);
    }
  }

  // 1. Diagnostics & Health
  public async getHealth(): Promise<SystemHealthResponse> {
    return this.request<SystemHealthResponse>('/health', { method: 'GET' }, 4000);
  }

  public async getReady(): Promise<SystemReadyResponse> {
    return this.request<SystemReadyResponse>('/ready', { method: 'GET' }, 5000);
  }

  // 2. RAG & MCP Query Engine
  public async queryRAG(req: QueryRequest): Promise<QueryResponse> {
    return this.request<QueryResponse>(
      '/query',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req),
      },
      60000 // 60s timeout for remote inference
    );
  }

  // 3. Document Lifecycle Management
  public async listDocuments(category?: string, status?: string): Promise<DocumentListResponse> {
    const params = new URLSearchParams();
    if (category && category !== 'all') params.append('category', category);
    if (status && status !== 'all') params.append('status', status);

    const queryStr = params.toString() ? `?${params.toString()}` : '';
    return this.request<DocumentListResponse>(`/documents${queryStr}`, { method: 'GET' }, 8000);
  }

  public async getDocument(documentId: string): Promise<DocumentSummary> {
    return this.request<DocumentSummary>(`/documents/${documentId}`, { method: 'GET' }, 6000);
  }

  public async uploadDocument(file: File, category: string): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    return this.request<DocumentUploadResponse>(
      '/documents',
      {
        method: 'POST',
        body: formData,
      },
      30000
    );
  }

  public async deleteDocument(documentId: string): Promise<DocumentDeleteResponse> {
    return this.request<DocumentDeleteResponse>(`/documents/${documentId}`, { method: 'DELETE' }, 10000);
  }

  // 4. Knowledge Base Telemetry
  public async getKnowledgeBaseStatus(): Promise<KnowledgeBaseStatusResponse> {
    return this.request<KnowledgeBaseStatusResponse>('/knowledge-base/status', { method: 'GET' }, 8000);
  }

  // 5. Active Learning & User Feedback
  public async submitFeedback(feedback: FeedbackSubmission): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>(
      '/feedback',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedback),
      },
      8000
    );
  }

  // 6. Analytics & Benchmarks
  public async getEvaluationSummary(): Promise<EvaluationSummaryResponse> {
    return this.request<EvaluationSummaryResponse>('/analytics/evaluation-summary', { method: 'GET' }, 8000);
  }
}

export const apiClient = new ApiClient();
