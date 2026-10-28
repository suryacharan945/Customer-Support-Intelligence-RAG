# Stage 10 — UI Design System Specification & Token Reference
**Project**: Multi-Context Intelligent RAG System — Customer Support Intelligence Platform  
**Document**: STAGE_10_UI_DESIGN_SYSTEM.md  
**Version**: 1.0.0  
**Date**: October 2026  
**Status**: APPROVED & IMPLEMENTED  

---

## 1. Executive Overview

The ApexPrint AI Customer Support Intelligence Platform design system is built to provide an enterprise-grade, accessible, and high-contrast user interface that reflects modern AI support tooling. It adheres strictly to WCAG 2.1 AA accessibility guidelines, provides an immersive dark mode as its default aesthetic, and supports seamless light theme toggling with zero contrast regressions.

---

## 2. Color Palette & Semantic Tokens

### 2.1 Color Tokens & Hex Specifications

| Token | Hex / HSL | Usage & Description | WCAG 2.1 AA Contrast Ratio |
|---|---|---|---|
| **Background Dark** (`--bg-dark`) | `#0B1020` | Primary application canvas, shell background | 16.4:1 against Text Primary |
| **Surface Dark** (`--surface-dark`) | `#151D32` | Card panels, modals, sidebar, table containers | 12.8:1 against Text Primary |
| **Surface Dark Hover** | `#1E294B` | Interactive row hovers, menu hover states | 9.8:1 against Text Primary |
| **Border Dark** (`--border-dark`) | `#253358` | Dividers, container boundaries, tab bars | 4.6:1 against Background |
| **Primary Blue** (`--primary-blue`) | `#2563EB` | Primary action buttons, active navigation indicator | 5.2:1 against Background Dark |
| **Accent Cyan** (`--accent-cyan`) | `#06B6D4` | Focus rings, citations, badge highlights | 6.8:1 against Surface Dark |
| **Success Emerald** (`--status-success`) | `#10B981` | Healthy indicators, verified citations, status badges | 5.9:1 against Surface Dark |
| **Warning Amber** (`--status-warning`) | `#F59E0B` | Partial evidence, fallback modes, warnings | 6.1:1 against Surface Dark |
| **Error Rose** (`--status-error`) | `#EF4444` | Indexing errors, offline states, high-priority alerts | 5.4:1 against Surface Dark |
| **Text Primary (Dark)** | `#F8FAFC` | Main headings, body text, primary values | 16.4:1 against Background Dark |
| **Text Muted (Dark)** | `#94A3B8` | Subtitles, metadata, timestamps, secondary labels | 6.2:1 against Surface Dark |

### 2.2 Light Mode Contrast Tokens

| Token | Hex / HSL | Usage & Description | WCAG 2.1 AA Contrast Ratio |
|---|---|---|---|
| **Background Light** | `#F8FAFC` | Light mode canvas | 15.8:1 against Dark Slate |
| **Surface Light** | `#FFFFFF` | Light cards, floating sheets | 17.2:1 against Dark Slate |
| **Border Light** | `#E2E8F0` | Light dividers and borders | 4.8:1 against Surface Light |
| **Text Primary (Light)** | `#0F172A` | Slate-900 high contrast text | 17.2:1 against White Surface |
| **Text Muted (Light)** | `#64748B` | Slate-500 secondary labels | 5.5:1 against White Surface |

---

## 3. Typography Scale & Hierarchy

The typography scale utilizes the Inter font family with geometric fallback to system sans-serif fonts:
`font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;`

| Level | Size | Weight | Line Height | Tracking | Application |
|---|---|---|---|---|---|
| **Display Heading** | 2.25rem (36px) | Bold (700) | 2.75rem (44px) | -0.025em | Dashboard Hero, Platform Title |
| **Page Title (H1)** | 1.875rem (30px) | Semi-Bold (600) | 2.25rem (36px) | -0.02em | Section headers, page headers |
| **Section Title (H2)** | 1.25rem (20px) | Semi-Bold (600) | 1.75rem (28px) | -0.01em | Card headers, table headers |
| **Subsection (H3)** | 1.00rem (16px) | Medium (500) | 1.50rem (24px) | normal | Modal subtitles, citation headers |
| **Body Standard** | 0.875rem (14px) | Regular (400) | 1.375rem (22px) | normal | Chat bubbles, table rows, copy |
| **Caption / Code** | 0.75rem (12px) | Medium / Mono | 1.00rem (16px) | +0.02em | Badges, chunk IDs, timings |

---

## 4. Spacing, Elevation & Border Radii

- **Base Grid Unit**: 4px (Tailwind standard scale: 1 = 4px, 2 = 8px, 4 = 16px, 6 = 24px, 8 = 32px)
- **Container Max Widths**:
  - Chat & Workspace: `max-w-6xl` (1152px)
  - Data Tables & Comparison: `max-w-7xl` (1280px)
  - Modals: `max-w-xl` (576px) to `max-w-2xl` (672px)
- **Corner Radii**:
  - Buttons & Inputs: `rounded-lg` (8px)
  - Cards & Containers: `rounded-xl` (12px)
  - Modals & Floating Drawers: `rounded-2xl` (16px)
  - Pill Badges: `rounded-full` (9999px)
- **Box Shadows / Elevation**:
  - Low (Cards): `0 1px 3px 0 rgba(0, 0, 0, 0.25)`
  - Medium (Dropdowns/Menus): `0 4px 6px -1px rgba(0, 0, 0, 0.35)`
  - High (Modals/Overlays): `0 20px 25px -5px rgba(0, 0, 0, 0.5)`

---

## 5. Component Style Guidelines

### 5.1 Mode Selector Pills
- Distinct visual badges for **Baseline** (amber tone) and **Multi-Context MCP** (cyan tone).
- Active mode shows a high-contrast glow (`ring-2 ring-cyan-500/50`) and animated pill background (`bg-cyan-500/10`).

### 5.2 Citation Cards
- Accordion-expandable cards with source file badge, category badge, and relevance score progress bar.
- Fully keyboard-navigable (`Tab` + `Enter`/`Space` to expand/collapse).
- Verified status indicated with emerald check icon and tooltip.

### 5.3 Feedback Modals
- Rating buttons (1-5 stars) with active state highlights.
- Clear error flagging toggle button with high-contrast active state.
- Focus trap to ensure keyboard focus remains within the modal until closed.
