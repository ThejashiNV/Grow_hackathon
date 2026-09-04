import { useEffect, useState } from "react";
import { api, type HealthResponse } from "./services/api";
import "./App.css";

function ServiceDot({ label, status }: { label: string; status: string }) {
  const color = status === "ok" ? "#22c55e" : status === "not_configured" ? "#a3a3a3" : "#ef4444";
  return (
    <span className="service-dot">
      <span className="dot" style={{ backgroundColor: color }} />
      {label}: {status}
    </span>
  );
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((err) => setError(err.message ?? "Backend unreachable"));
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Smart Watch</h1>
        <p className="tagline">What changed since you last checked?</p>
      </header>

      <nav className="app-nav">
        <span className="nav-item active">Attention</span>
        <span className="nav-item">Watchlist</span>
        <span className="nav-item">History</span>
      </nav>

      <main className="app-main">
        <h2>Backend connectivity</h2>
        {error && <p className="error">Could not reach backend: {error}</p>}
        {health && (
          <div className="health-panel">
            <p>API status: {health.status}</p>
            <ServiceDot label="MongoDB" status={health.services.mongodb} />
            <ServiceDot label="Redis" status={health.services.redis} />
            <ServiceDot label="Chroma" status={health.services.chroma} />
          </div>
        )}
        {!health && !error && <p>Checking backend...</p>}
      </main>
    </div>
  );
}

export default App;
