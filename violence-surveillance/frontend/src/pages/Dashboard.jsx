/**
 * Centre de surveillance — page unique (stats, caméras, alertes)
 */

import { useState, useEffect, useCallback } from "react";
import { API, recordingsUrl } from "../config";
import { formatDateTime, timeAgo, confidenceLevel } from "../utils/format";
import VideoFeed from "../components/VideoFeed";

const REFRESH_CAMERAS = 5000;
const REFRESH_ALERTS = 5000;

export default function Dashboard() {
  const [cameras, setCameras] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [form, setForm] = useState({ name: "", location: "", url: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [apiOnline, setApiOnline] = useState(true);

  const fetchCameras = useCallback(async () => {
    try {
      const res = await fetch(`${API}/cameras`);
      if (!res.ok) throw new Error();
      setCameras(await res.json());
      setApiOnline(true);
    } catch {
      setApiOnline(false);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch(`${API}/alerts`);
      if (!res.ok) throw new Error();
      setAlerts(await res.json());
    } catch {
      /* silencieux — fetchCameras gère le statut API */
    }
  }, []);

  useEffect(() => {
    fetchCameras();
    fetchAlerts();
    const camInterval = setInterval(fetchCameras, REFRESH_CAMERAS);
    const alertInterval = setInterval(fetchAlerts, REFRESH_ALERTS);
    return () => {
      clearInterval(camInterval);
      clearInterval(alertInterval);
    };
  }, [fetchCameras, fetchAlerts]);

  const activeCameras = cameras.filter((c) => c.is_active);
  const liveCount = activeCameras.length;

  const handleAdd = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.name.trim() || !form.url.trim()) {
      setError("Nom et flux vidéo requis");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API}/cameras`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error();
      setForm({ name: "", location: "", url: "" });
      fetchCameras();
    } catch {
      setError("Erreur lors de l'ajout de la caméra");
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (id) => {
    await fetch(`${API}/cameras/${id}/toggle`, { method: "PATCH" });
    fetchCameras();
  };

  const markReviewed = async (id) => {
    await fetch(`${API}/alerts/${id}/review`, { method: "PATCH" });
    fetchAlerts();
  };

  return (
    <>
      {/* ── Statistiques ─────────────────────────────────────── */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon cameras">📷</div>
          <div className="stat-content">
            <span className="stat-label">Caméras actives</span>
            <span className="stat-value">{activeCameras.length}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon live">🟢</div>
          <div className="stat-content">
            <span className="stat-label">En direct</span>
            <span className="stat-value">{liveCount}</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon alerts">🚨</div>
          <div className="stat-content">
            <span className="stat-label">Incidents détectés</span>
            <span className="stat-value">{alerts.length}</span>
          </div>
        </div>
      </div>

      {/* ── Ajouter une caméra ───────────────────────────────── */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <span className="section-title-bar" />
            Ajouter une caméra
          </h2>
        </div>
        <div className="form-card">
          {error && <p className="form-error">{error}</p>}
          <form className="form-grid" onSubmit={handleAdd}>
            <div className="form-field">
              <label htmlFor="cam-name">Nom</label>
              <input
                id="cam-name"
                placeholder="Entrée principale"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div className="form-field full">
              <label htmlFor="cam-url">Flux (RTSP ou fichier vidéo)</label>
              <input
                id="cam-url"
                placeholder="rtsp://user:pass@192.168.1.10:554/stream1 ou 0 (webcam)"
                value={form.url}
                onChange={(e) => setForm({ ...form, url: e.target.value })}
              />
            </div>
            <div className="form-field">
              <label htmlFor="cam-location">Emplacement</label>
              <input
                id="cam-location"
                placeholder="Parking nord"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Démarrage…" : "▶ Démarrer"}
            </button>
          </form>
        </div>
      </section>

      {/* ── Caméras actives ──────────────────────────────────── */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <span className="section-title-bar" />
            Caméras actives
          </h2>
          <span className="section-badge">
            {activeCameras.length} caméra{activeCameras.length !== 1 ? "s" : ""}
          </span>
        </div>

        {cameras.length === 0 ? (
          <div className="empty-state">
            <strong>Aucune caméra configurée</strong>
            Ajoutez un flux ci-dessus pour démarrer la surveillance.
          </div>
        ) : (
          <div className="camera-grid">
            {cameras.map((cam) => (
              <div key={cam.id} className="camera-card">
                {cam.is_active ? (
                  <VideoFeed camera={cam} />
                ) : (
                  <div className="camera-video-wrap camera-offline">
                    <span className="offline-badge">Hors ligne</span>
                  </div>
                )}
                <div className="camera-info">
                  <div className="camera-meta">
                    <h3>{cam.name}</h3>
                    {cam.location && <p className="location">{cam.location}</p>}
                    <p className="url">{cam.url}</p>
                  </div>
                  <button
                    type="button"
                    className={cam.is_active ? "btn btn-danger" : "btn btn-primary"}
                    onClick={() => handleToggle(cam.id)}
                  >
                    {cam.is_active ? "⏹ Arrêter" : "▶ Démarrer"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Incidents détectés ───────────────────────────────── */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <span className="section-title-bar" />
            Incidents détectés
          </h2>
          <span className="section-badge">
            {alerts.length} incident{alerts.length !== 1 ? "s" : ""}
          </span>
        </div>

        {alerts.length === 0 ? (
          <div className="empty-state">
            <strong>Aucun incident enregistré</strong>
            Les alertes de violence apparaîtront ici automatiquement.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="alerts-table">
              <thead>
                <tr>
                  <th>Caméra</th>
                  <th>Image</th>
                  <th>Confiance</th>
                  <th>Dernière détection</th>
                  <th>Statut</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => {
                  const pct = Math.round(alert.confidence * 100);
                  const level = confidenceLevel(pct);
                  const thumb = alert.thumbnail_path
                    ? recordingsUrl(alert.thumbnail_path.split(/[/\\]/).pop())
                    : null;

                  return (
                    <tr key={alert.id} className={!alert.reviewed ? "unreviewed" : ""}>
                      <td>
                        <span className="camera-tag">📷 {alert.camera_name}</span>
                      </td>
                      <td>
                        {thumb ? (
                          <a href={thumb} target="_blank" rel="noreferrer">
                            <img src={thumb} alt="incident" className="alert-thumb" />
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="confidence-cell">
                        <div className={`confidence-value ${level}`}>{pct}%</div>
                        <div className="confidence-bar">
                          <div
                            className={`confidence-fill ${level}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </td>
                      <td className="time-cell">
                        <div className="time-main">{formatDateTime(alert.detected_at)}</div>
                        <div className="time-ago">{timeAgo(alert.detected_at)}</div>
                      </td>
                      <td>
                        <span className={`status-badge ${alert.reviewed ? "reviewed" : "pending"}`}>
                          {alert.reviewed ? "✔ Vérifié" : "● En attente"}
                        </span>
                      </td>
                      <td>
                        <div className="table-actions">
                          {alert.clip_path && (
                            <a
                              href={recordingsUrl(alert.clip_path.split(/[/\\]/).pop())}
                              target="_blank"
                              rel="noreferrer"
                              className="clip-link"
                            >
                              📥 Clip
                            </a>
                          )}
                          {!alert.reviewed && (
                            <button
                              type="button"
                              className="btn btn-success"
                              onClick={() => markReviewed(alert.id)}
                            >
                              ✓ Vérifier
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <footer className="app-footer">
        Rafraîchissement automatique — Caméras : {REFRESH_CAMERAS / 1000}s · Incidents :{" "}
        {REFRESH_ALERTS / 1000}s · Aperçu live : 1s
        {!apiOnline && " · ⚠ API hors ligne"}
      </footer>
    </>
  );
}
