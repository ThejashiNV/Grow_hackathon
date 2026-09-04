import { NavLink, Route, HashRouter as Router, Routes } from "react-router-dom";
import { AttentionPage } from "./pages/AttentionPage";
import { HistoryPage } from "./pages/HistoryPage";
import { WatchlistPage } from "./pages/WatchlistPage";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="app-shell">
        <header className="app-header">
          <h1>Smart Watch</h1>
          <p className="tagline">What changed since you last checked?</p>
        </header>

        <nav className="app-nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
            Attention
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
            History
          </NavLink>
          <NavLink to="/watchlist" className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
            Watchlist
          </NavLink>
        </nav>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<AttentionPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
