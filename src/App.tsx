/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { PublicLayout } from './layouts/PublicLayout';
import { AppLayout } from './layouts/AppLayout';
import { HomePage } from './pages/HomePage';
import { DemoPage } from './pages/DemoPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { DocsPage } from './pages/DocsPage';
import { OverviewPage } from './pages/OverviewPage';
import { AnalyzePage } from './pages/AnalyzePage';
import { RunsPage } from './pages/RunsPage';
import { NotFoundPage } from './pages/NotFoundPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes under PublicLayout */}
        <Route element={<PublicLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/demo" element={<DemoPage />} />
          <Route path="/architecture" element={<ArchitecturePage />} />
          <Route path="/docs" element={<DocsPage />} />
        </Route>

        {/* Console / App Routes under AppLayout */}
        <Route element={<AppLayout />}>
          <Route path="/app/overview" element={<OverviewPage />} />
          <Route path="/app/analyze" element={<AnalyzePage />} />
          <Route path="/app/runs" element={<RunsPage />} />
        </Route>

        {/* Catch-all Not Found Route */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
