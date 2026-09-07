import { NavLink, Route, HashRouter as Router, Routes } from "react-router-dom";
import { ParticleField } from "./components/ParticleField";
import { AttentionPage } from "./pages/AttentionPage";
import { DailyFeedPage } from "./pages/DailyFeedPage";
import { HistoryPage } from "./pages/HistoryPage";
import { IntelligencePage } from "./pages/IntelligencePage";
import { WatchlistPage } from "./pages/WatchlistPage";
import "./App.css";

function App() {
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
      </div>
    </Router>
  );
}

export default App;
