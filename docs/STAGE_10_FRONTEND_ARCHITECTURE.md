# Stage 10 — Frontend Architecture & Component Specification
**Project**: Multi-Context Intelligent RAG System — Customer Support Intelligence Platform  
**Document**: STAGE_10_FRONTEND_ARCHITECTURE.md  
**Version**: 1.0.0  
**Date**: October 2026  
**Status**: APPROVED & IMPLEMENTED  

---

## 1. Architectural Overview

The frontend architecture follows a modern single-page application (SPA) design implemented in **React 18/19**, **TypeScript**, and **Vite**. It provides modular separation between API communication, global presentation state, domain components, and routing.

```
+-------------------------------------------------------------------------+
|                                AppShell                                 |
|  +--------------------+-----------------------------------------------+  |
|  |     Sidebar        |                   Header                      |  |
|  |  - Brand & Logo    |  - Page Title & Breadcrumbs                   |  |
|  |  - 7 Navigation    |  - Ready Status Pill (5-point deep probe)     |  |
|  |    Links           |  - Dark / Light Theme Toggle                  |  |
|  |  - Drive & Storage |  - API Connection Indicator                   |  |
|  |    Telemetry       +-----------------------------------------------+  |
|  |                    |                   Main Content                |  |
|  |                    |  +-----------------------------------------+  |  |
|  |                    |  | Dashboard | Chat | Documents | Comp     |  |  |
|  |                    |  | Analytics | HowItWorks | Status         |  |  |
|  |                    |  +-----------------------------------------+  |  |
|  +--------------------+-----------------------------------------------+  |
+-------------------------------------------------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
+-----------------------+                       +-----------------------+
|      React Router     |                       |    Context State      |
|  / (Dashboard)        |                       |  - ThemeContext       |
|  /chat (AI Assistant) |                       |  - ChatContext        |
|  /documents (Studio)  |                       +-----------------------+
|  /compare (Dual Run)  |                                   |
|  /analytics (Metrics) |                       +-----------------------+
|  /how-it-works (Guide)|                       |    apiClient (Fetch)  |
|  /status (Diagnostics)|                       |  - AbortController    |
+-----------------------+                       |  - Strict TypeScript  |
                                                |  - Error Mapping      |
                                                +-----------------------+
                                                            |
                                                +-----------------------+
                                                |  FastAPI Backend      |
                                                |  (http://127.0.0.1)   |
                                                +-----------------------+
```

---

## 2. Directory Hierarchy

```
web/
├── index.html                   # HTML entry point with meta tags & fonts
├── package.json                 # Project dependencies & scripts
├── postcss.config.js            # PostCSS plugin pipeline
├── tailwind.config.js           # Design system tokens and styling extensions
├── tsconfig.json                # Project-wide TypeScript configuration
├── tsconfig.app.json            # Application TypeScript configuration
├── tsconfig.node.json           # Build-time TypeScript configuration
├── vite.config.ts               # Vite bundler, proxy configuration & vitest setup
└── src/
    ├── main.tsx                 # React DOM mount point
    ├── App.tsx                  # BrowserRouter & Route declarations
    ├── index.css                # Tailwind base styles and CSS custom properties
    ├── vite-env.d.ts            # Vite client type definitions
    ├── api/
    │   ├── types.ts             # Pydantic-mirrored TypeScript interfaces
    │   └── client.ts            # Singleton API client with timeout & error handling
    ├── context/
    │   ├── ThemeContext.tsx     # Dark/Light theme provider with localStorage sync
    │   └── ChatContext.tsx      # Conversation state, active RAG mode, message history
    ├── components/
    │   ├── common/              # Reusable primitive UI components
    │   │   ├── Badge.tsx        # Status, category, and evidence badges
    │   │   ├── Button.tsx       # Accessible button with loading spinners
    │   │   ├── Card.tsx         # Card container with title and action headers
    │   │   ├── Modal.tsx        # Radix UI dialog with focus trap
    │   │   ├── Skeleton.tsx     # Loading placeholders
    │   │   └── Tooltip.tsx      # Hover and focus accessible tooltips
    │   ├── layout/              # Shell and navigation components
    │   │   ├── AppShell.tsx     # Responsive layout wrapper with sidebar and header
    │   │   ├── Header.tsx       # Top navigation bar with readiness badge & theme toggle
    │   │   └── Sidebar.tsx      # Side navigation with storage bar and collapsed state
    │   ├── chat/                # AI Chat components
    │   │   ├── ChatMessage.tsx  # Message bubble with markdown & citation rendering
    │   │   ├── CitationCard.tsx # Expandable evidence cards with relevance score
    │   │   ├── FeedbackModal.tsx# Modal for ratings and correction submission
    │   │   └── ModeSelector.tsx # Baseline vs Multi-Context toggle control
    │   ├── documents/           # Document management components
    │   │   ├── DocumentTable.tsx# Sortable, filterable document registry table
    │   │   ├── DocumentDetailModal.tsx # Document metadata & chunk inspect modal
    │   │   └── UploadDropzone.tsx # Drag-and-drop file upload with validation
    │   └── 3d/                  # Visual knowledge graph representations
    │       ├── KnowledgeHero3D.tsx # Three.js/R3F interactive particle network
    │       └── FallbackStaticHero.tsx # Accessible 2D canvas fallback
    ├── pages/                   # Application route pages
    │   ├── DashboardPage.tsx    # Platform overview, KPIs, and quick actions
    │   ├── ChatPage.tsx         # Support chat assistant with session controls
    │   ├── DocumentsPage.tsx    # Knowledge Base Studio & document uploads
    │   ├── ComparisonPage.tsx   # Dual-channel side-by-side RAG evaluation
    │   ├── AnalyticsPage.tsx    # Recharts benchmark dashboards and audit insights
    │   ├── HowItWorksPage.tsx   # Educational guide explaining RAG vs MCP
    │   └── SystemStatusPage.tsx # 5-point subsystem readiness probe
    └── test/                    # Unit and integration test suite
        ├── setup.ts             # Test environment configuration & polyfills
        ├── App.test.tsx         # Application mount and route tests
        └── Components.test.tsx  # Interactive UI component test suite
```

---

## 3. State Management & Lifecycle

1. **ThemeContext**:
   - Manages dark/light theme state.
   - Synchronizes with `localStorage` and system `prefers-color-scheme`.
   - Modifies the `.dark` class on `document.documentElement` to trigger Tailwind's class-based dark mode.

2. **ChatContext**:
   - Maintains conversation message history array (`messages`).
   - Tracks active `retrievalMode` (`'baseline'` | `'multi_context'`).
   - Holds active `sessionId` to maintain conversation context across queries.
   - Tracks `isLoading` to disable duplicate submissions.
   - Handles feedback modal targeting (`feedbackModalOpen`, `activeFeedbackQueryId`).

3. **Local Component State**:
   - Documents page manages table search, category filter, selection, and delete/upload modal state.
   - Comparison page manages independent dual query execution and side-by-side metric calculations.
   - Analytics page handles benchmark tab switching (Development vs Held-Out).

---

## 4. API Client Architecture

The `apiClient` class provides a unified layer for communicating with the FastAPI backend:
- Configured with relative base URL (`/api/v1`) in development, taking advantage of Vite's reverse proxy to prevent CORS issues.
- Supports configurable timeouts with `AbortController` (4s for health checks, 30s for document indexing, 60s for LLM inference).
- Maps backend errors into structured `ApiClientError` instances that preserve HTTP status codes and validation details.
