import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AlertsPage } from "./pages/AlertsPage";
import { CollectorPage } from "./pages/CollectorPage";
import { Dashboard } from "./pages/Dashboard";
import { SettingsPage } from "./pages/SettingsPage";
import type { AnalyzeDraft, AnalyzeResponse, ArchivedAlert } from "./types/threat";
import {
  buildArchivedAlerts,
  loadArchivedAlerts,
  saveArchivedAlerts,
} from "./utils/alertStorage";

const defaultDraft: AnalyzeDraft = {
  source: "github",
  query: "acme password",
  raw_text: "AWS_SECRET_ACCESS_KEY=abcd1234example",
};

export default function App() {
  const [draft, setDraft] = useState<AnalyzeDraft>(defaultDraft);
  const [archivedAlerts, setArchivedAlerts] = useState<ArchivedAlert[]>(() =>
    loadArchivedAlerts(),
  );

  useEffect(() => {
    saveArchivedAlerts(archivedAlerts);
  }, [archivedAlerts]);

  const handleAnalyzeSuccess = (response: AnalyzeResponse) => {
    const timestamp = new Date().toISOString();
    const nextAlerts = buildArchivedAlerts(response, timestamp);
    if (nextAlerts.length === 0) return;
    setArchivedAlerts((current) => [...nextAlerts, ...current]);
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Dashboard
              draft={draft}
              onDraftChange={setDraft}
              onAnalyzeSuccess={handleAnalyzeSuccess}
            />
          }
        />
        <Route
          path="/collector"
          element={<CollectorPage onSendToAnalyzeDraft={setDraft} />}
        />
        <Route
          path="/alerts"
          element={
            <AlertsPage
              alerts={archivedAlerts}
              onClearAlerts={() => setArchivedAlerts([])}
            />
          }
        />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
