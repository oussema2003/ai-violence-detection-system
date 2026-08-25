import { useState, useEffect } from "react";
import { API, recordingsUrl } from "../config";

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);

  const fetchAlerts = async () => {
    const res = await fetch(`${API}/alerts`);
    setAlerts(await res.json());
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5000); // refresh auto toutes les 5s
    return () => clearInterval(interval);
  }, []);

  const markReviewed = async (id) => {
    await fetch(`${API}/alerts/${id}/review`, { method: "PATCH" });
    fetchAlerts();
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif", background: "#0f172a", minHeight: "100vh", color: "#f1f5f9" }}>
      <h1>🚨 Historique des incidents</h1>

      {alerts.length === 0 && (
        <p style={{ color: "#64748b" }}>Aucun incident enregistré pour le moment.</p>
      )}

      <div style={{ display: "grid", gap: "1rem" }}>
        {alerts.map(alert => (
          <div key={alert.id} style={{
            background: alert.reviewed ? "#1e293b" : "#450a0a",
            border: `1px solid ${alert.reviewed ? "#334155" : "#dc2626"}`,
            borderRadius: 8, padding: "1rem"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>📷 {alert.camera_name}</strong>
                <span style={{ marginLeft: 16, color: "#94a3b8", fontSize: 13 }}>
                  {new Date(alert.detected_at).toLocaleString("fr-FR")}
                </span>
              </div>
              <span style={{
                background: "#dc2626", color: "#fff",
                padding: "3px 12px", borderRadius: 12, fontSize: 13
              }}>
                Confiance : {(alert.confidence * 100).toFixed(1)}%
              </span>
            </div>

            {/* Thumbnail */}
            {alert.thumbnail_path && (
              <img
                src={recordingsUrl(alert.thumbnail_path.split(/[/\\]/).pop())}
                alt="incident"
                style={{ marginTop: 10, maxWidth: 320, borderRadius: 6 }}
              />
            )}

            {alert.clip_path && (
              <div style={{ marginTop: 8 }}>
                <a
                  href={recordingsUrl(alert.clip_path.split(/[/\\]/).pop())}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: "#60a5fa", fontSize: 13 }}
                >
                  📥 Télécharger le clip vidéo
                </a>
              </div>
            )}
            {!alert.reviewed && (
              <button
                onClick={() => markReviewed(alert.id)}
                style={{ marginTop: 10, padding: "6px 14px", background: "#16a34a", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer" }}
              >
                ✅ Marquer comme vérifié
              </button>
            )}
            {alert.reviewed && <p style={{ color: "#4ade80", marginTop: 8, fontSize: 13 }}>✔ Vérifié</p>}
          </div>
        ))}
      </div>
    </div>
  );
}