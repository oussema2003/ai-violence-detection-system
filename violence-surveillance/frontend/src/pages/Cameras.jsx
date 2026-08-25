/**
 * Page de gestion des caméras — ajout, suppression, activation
 */

import { useState, useEffect } from "react";
import { API } from "../config";

export default function Cameras() {
  const [cameras, setCameras]   = useState([]);
  const [form, setForm]         = useState({ name: "", location: "", url: "" });
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  // ── Charger les caméras ───────────────────────────────────────
  const fetchCameras = async () => {
    const res = await fetch(`${API}/cameras`);
    setCameras(await res.json());
  };

  useEffect(() => { fetchCameras(); }, []);

  // ── Ajouter une caméra ────────────────────────────────────────
  const handleAdd = async (e) => {
    e.preventDefault();
    setError("");
    if (!form.name || !form.url) { setError("Nom et URL requis"); return; }

    setLoading(true);
    const res = await fetch(`${API}/cameras`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setLoading(false);

    if (res.ok) {
      setForm({ name: "", location: "", url: "" });
      fetchCameras();
    } else {
      setError("Erreur lors de l'ajout");
    }
  };

  // ── Supprimer ─────────────────────────────────────────────────
  const handleDelete = async (id) => {
    if (!confirm("Supprimer cette caméra ?")) return;
    await fetch(`${API}/cameras/${id}`, { method: "DELETE" });
    fetchCameras();
  };

  // ── Activer/Désactiver ────────────────────────────────────────
  const handleToggle = async (id) => {
    await fetch(`${API}/cameras/${id}/toggle`, { method: "PATCH" });
    fetchCameras();
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>🎥 Gestion des caméras</h1>

      {/* ── Formulaire d'ajout ─────────────────────────────── */}
      <div style={{ background: "#f5f5f5", padding: "1rem", borderRadius: 8, marginBottom: "2rem" }}>
        <h2>Ajouter une caméra</h2>
        {error && <p style={{ color: "red" }}>{error}</p>}

        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <input
            placeholder="Nom (ex: Entrée principale)"
            value={form.name}
            onChange={e => setForm({ ...form, name: e.target.value })}
            style={inputStyle}
          />
          <input
            placeholder="Emplacement (optionnel)"
            value={form.location}
            onChange={e => setForm({ ...form, location: e.target.value })}
            style={inputStyle}
          />
          <input
            placeholder="URL — rtsp://... ou 0 (webcam)"
            value={form.url}
            onChange={e => setForm({ ...form, url: e.target.value })}
            style={{ ...inputStyle, minWidth: "300px" }}
          />
          <button onClick={handleAdd} disabled={loading} style={btnStyle("#2563eb")}>
            {loading ? "Ajout..." : "➕ Ajouter"}
          </button>
        </div>
      </div>

      {/* ── Liste des caméras ──────────────────────────────── */}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "#e2e8f0" }}>
            <th style={th}>Nom</th>
            <th style={th}>Emplacement</th>
            <th style={th}>URL</th>
            <th style={th}>Statut</th>
            <th style={th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {cameras.map(cam => (
            <tr key={cam.id} style={{ borderBottom: "1px solid #ddd" }}>
              <td style={td}>{cam.name}</td>
              <td style={td}>{cam.location}</td>
              <td style={td}><code>{cam.url}</code></td>
              <td style={td}>
                <span style={{
                  padding: "2px 10px",
                  borderRadius: 12,
                  background: cam.is_active ? "#dcfce7" : "#fee2e2",
                  color:      cam.is_active ? "#16a34a" : "#dc2626",
                }}>
                  {cam.is_active ? "Actif" : "Inactif"}
                </span>
              </td>
              <td style={td}>
                <button onClick={() => handleToggle(cam.id)} style={btnStyle("#6366f1")}>
                  {cam.is_active ? "Désactiver" : "Activer"}
                </button>{" "}
                <button onClick={() => handleDelete(cam.id)} style={btnStyle("#ef4444")}>
                  Supprimer
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Styles inline minimalistes ─────────────────────────────────────
const inputStyle = { padding: "8px 12px", borderRadius: 6, border: "1px solid #cbd5e1", fontSize: 14 };
const btnStyle   = (bg) => ({ padding: "8px 14px", borderRadius: 6, background: bg, color: "#fff", border: "none", cursor: "pointer", fontSize: 13 });
const th = { padding: "10px", textAlign: "left" };
const td = { padding: "10px" };