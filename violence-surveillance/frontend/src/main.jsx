import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import Dashboard from "./pages/Dashboard";
import { API } from "./config";
import "./styles/app.css";

function AppHeader({ apiOnline }) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="header-logo">🛡️</div>
        <div className="header-titles">
          <span className="header-subtitle">Surveillance violence</span>
          <span className="header-title">Centre de surveillance</span>
        </div>
      </div>
      <div className="api-status">
        <span className={`api-dot ${apiOnline ? "" : "offline"}`} />
        {apiOnline ? "API en ligne" : "API hors ligne"}
      </div>
    </header>
  );
}

function App() {
  const [apiOnline, setApiOnline] = useState(true);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${API}/cameras`);
        setApiOnline(res.ok);
      } catch {
        setApiOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <AppHeader apiOnline={apiOnline} />
      <main className="app-main">
        <Dashboard />
      </main>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
