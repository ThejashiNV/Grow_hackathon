import { useEffect, useState } from "react";
import { NavLink, Route, HashRouter as Router, Routes } from "react-router-dom";
import { ParticleField } from "./components/ParticleField";
import { api } from "./services/api";
import { AttentionPage } from "./pages/AttentionPage";
import { DailyFeedPage } from "./pages/DailyFeedPage";
import { HistoryPage } from "./pages/HistoryPage";
import { IntelligencePage } from "./pages/IntelligencePage";
import { WatchlistPage } from "./pages/WatchlistPage";
import "./App.css";

function App() {
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    api.getAttention()
      .then(res => {
        setAlertCount(res.items.filter(i => i.bundle.is_meaningful).length);
      })
      .catch(() => {});
  }, []);

  return (
    <Router>
      <ParticleField />
      <div className="app-shell">
        <header className="app-header">
          <h1>GROW</h1>
          <p className="tagline">Smart Market Intelligence Terminal</p>
          <div className="header-status">
            <span className="header-dot" />
            LIVE
          </div>
        </header>

        <nav className="app-nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
            Attention
            {alertCount > 0 && <span className="nav-badge">{alertCount}</span>}
          </NavLink>
          <NavLink to="/feed" className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
            Daily Feed
          </NavLink>
          <NavLink to="/watchlist" className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
            Watchlist
          </NavLink>
          <NavLink to="/intelligence" className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
            Intelligence
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
            History
          </NavLink>
        </nav>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<AttentionPage />} />
            <Route path="/feed" element={<DailyFeedPage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
            <Route path="/intelligence" element={<IntelligencePage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>

        <footer className="app-footer">
          <span>GROW v1.0</span>
          <span className="footer-sep">·</span>
          <span>18 NSE Stocks</span>
          <span className="footer-sep">·</span>
          <span>Multi-Horizon Analysis</span>
          <span className="footer-sep">·</span>
          <span>Pattern Discovery</span>
        </footer>
      </div>
    </Router>
  );
}

export default App;
