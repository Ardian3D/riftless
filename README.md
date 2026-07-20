# RIFTLESS — Change Guardian Client

RIFTLESS is a context-aware autonomous data change guardian. It detects the organizational blast radius of schema and pipeline changes, validates compatibility, and helps engineering teams understand downstream impacts before code is merged.

This repository contains the completed frontend foundation for RIFTLESS.

## 🛠️ Frontend Stack

- **Framework**: React 19 (Functional Components with hooks)
- **Build Tool**: Vite 6 (Fast, modern developer loop)
- **Language**: TypeScript (Strict type checks)
- **Styling**: Tailwind CSS v4 (Design tokens & responsive utility classes)
- **Routing**: React Router DOM v7 (Clean client-side routing)
- **Icons**: Lucide React

---

## 🚀 Getting Started

Follow these commands to install dependencies, run the application in development, and perform linting or production builds.

### 1. Install Dependencies
```bash
npm install
```

### 2. Run in Development Mode
Starts the Vite dev server locally on port 3000.
```bash
npm run dev
```

### 3. Build for Production
Compiles the application to optimized static assets in the `/dist` folder.
```bash
npm run build
```

### 4. Code Quality & Typechecking
Run both lint checks and TypeScript compiler validation:
```bash
npm run lint
```
*(This maps to `tsc --noEmit` as configured in the foundation to guarantee complete type-safety across all components).*

---

## 📍 Application Routes

RIFTLESS features two layout zones (Public Marketing/Docs and Application Console Pages) with full responsive support for screen sizes down to 360px:

### Public Pages
- `/*` — Catch-all custom Not Found handler
- `/` — Homepage / Brand Identity Swatch & Console launcher
- `/demo` — Interactive demo experience blueprint
- `/architecture` — Lineage Retriever & SQLGlot integration system architecture
- `/docs` — Getting started guide and local installation commands

### Application Console Pages
- `/app/overview` — Status badges inventory, metric previews, and interactive state simulation controls
- `/app/analyze` — Change analysis diff paste interface (Locked state)
- `/app/runs` — Run history audit overview and pull request lists

---

## 📊 Phase F0 Completion Status

Phase F0 is **fully complete**.
- **Visual Foundation**: Design tokens (`tokens.css`), custom fonts (Inter, Space Grotesk, JetBrains Mono), and visual styles are set up and integrated.
- **Feedback & Status Components**: `StatusBadge`, `LoadingState`, `EmptyState`, and `ErrorState` components are built, fully tested, keyboard-accessible, and supports reduced-motion.
- **Navigation & Layouts**: Flexible desktop/mobile-optimized layouts are established with reactive route indicators.
- **Mock Data**: Real-world metrics are removed or safely labeled with `—` and `COMPONENT PREVIEW` flags to maintain absolute honesty.

> ⚠️ **Backend Services Notice**: FastAPI, Python engines, deep-remediation solvers, SQLite storage, and the live DataHub writeback features are currently out of scope for this frontend foundation phase and will be implemented in subsequent phases.
