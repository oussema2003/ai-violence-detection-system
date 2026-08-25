# 📡 Documentation API

Documentation complète de l'API REST et WebSocket du système de surveillance de violence.

## 🔗 Base URLs

- **Développement** : `http://localhost:8000`
- **Production** : `https://votre-domaine.com/api`
- **WebSocket** : `ws://localhost:8000/ws`

## 📚 Documentation interactive

- **Swagger UI** : `http://localhost:8000/docs`
- **ReDoc** : `http://localhost:8000/redoc`
- **OpenAPI Schema** : `http://localhost:8000/openapi.json`

## 🔐 Authentification

> **Note** : La version actuelle n'implémente pas d'authentification. Pour la production, ajoutez OAuth2/JWT.

Future implementation :
```http
Authorization: Bearer <your-token>
```

## 📹 Endpoints Caméras

### GET /api/cameras

Liste toutes les caméras enregistrées.

**Request :**
```http
GET /api/cameras HTTP/1.1
Host: localhost:8000
```

**Response :**
```json
[
  {
    "id": 1,
    "name": "Entrée principale",
    "location": "Bâtiment A - RDC",
    "url": "rtsp://192.168.1.100:554/stream",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Parking",
    "location": "Extérieur",
    "url": "rtsp://192.168.1.101:554/stream",
    "is_active": false
  }
]
```

**Codes de statut :**
- `200 OK` : Succès
- `500 Internal Server Error` : Erreur serveur

---

### POST /api/cameras

Ajoute une nouvelle caméra au système.

**Request :**
```http
POST /api/cameras HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "name": "Caméra couloir",
  "location": "Étage 2",
  "url": "rtsp://192.168.1.102:554/stream"
}
```

**Request Body Schema :**
| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `name` | string | ✅ | Nom de la caméra |
| `location` | string | ❌ | Emplacement physique |
| `url` | string | ✅ | URL du flux vidéo (RTSP, HTTP, fichier) |

**Response :**
```json
{
  "id": 3,
  "name": "Caméra couloir",
  "location": "Étage 2",
  "url": "rtsp://192.168.1.102:554/stream",
  "is_active": true
}
```

**Codes de statut :**
- `200 OK` : Caméra créée avec succès
- `422 Unprocessable Entity` : Données invalides
- `500 Internal Server Error` : Erreur serveur

**Exemples cURL :**

```bash
# Ajouter une caméra RTSP
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Caméra 1",
    "location": "Hall",
    "url": "rtsp://admin:password@192.168.1.100:554/stream"
  }'

# Ajouter une caméra HTTP
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Webcam",
    "url": "http://192.168.1.200:8080/video"
  }'

# Ajouter un fichier vidéo (test)
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vidéo test",
    "url": "/app/test_videos/sample.mp4"
  }'
```

---

### DELETE /api/cameras/{camera_id}

Supprime une caméra du système.

**Request :**
```http
DELETE /api/cameras/3 HTTP/1.1
Host: localhost:8000
```

**Response :**
```json
{
  "detail": "Caméra supprimée"
}
```

**Codes de statut :**
- `200 OK` : Caméra supprimée
- `404 Not Found` : Caméra introuvable
- `500 Internal Server Error` : Erreur serveur

**Exemple cURL :**
```bash
curl -X DELETE http://localhost:8000/api/cameras/3
```

---

### PATCH /api/cameras/{camera_id}/toggle

Active ou désactive une caméra.

**Request :**
```http
PATCH /api/cameras/1/toggle HTTP/1.1
Host: localhost:8000
```

**Response :**
```json
{
  "is_active": false
}
```

**Codes de statut :**
- `200 OK` : Statut modifié
- `404 Not Found` : Caméra introuvable
- `500 Internal Server Error` : Erreur serveur

**Exemple cURL :**
```bash
# Activer/désactiver la caméra 1
curl -X PATCH http://localhost:8000/api/cameras/1/toggle
```

---

## 🚨 Endpoints Alertes

### GET /api/alerts

Liste les alertes de violence détectées.

**Request :**
```http
GET /api/alerts?skip=0&limit=50 HTTP/1.1
Host: localhost:8000
```

**Query Parameters :**
| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `skip` | integer | 0 | Nombre d'alertes à ignorer (pagination) |
| `limit` | integer | 50 | Nombre maximum d'alertes à retourner |

**Response :**
```json
[
  {
    "id": 1,
    "camera_id": 1,
    "camera_name": "Entrée principale",
    "confidence": 0.89,
    "detected_at": "2024-01-15T14:32:10.123456",
    "clip_path": "/recordings/camera_1_20240115_143210.mp4",
    "thumbnail_path": "/recordings/camera_1_20240115_143210_thumb.jpg",
    "reviewed": false,
    "notes": ""
  },
  {
    "id": 2,
    "camera_id": 1,
    "camera_name": "Entrée principale",
    "confidence": 0.92,
    "detected_at": "2024-01-15T15:45:30.654321",
    "clip_path": "/recordings/camera_1_20240115_154530.mp4",
    "thumbnail_path": "/recordings/camera_1_20240115_154530_thumb.jpg",
    "reviewed": true,
    "notes": "Incident confirmé - rapport envoyé"
  }
]
```

**Codes de statut :**
- `200 OK` : Succès
- `500 Internal Server Error` : Erreur serveur

**Exemples cURL :**

```bash
# Récupérer les 20 dernières alertes
curl http://localhost:8000/api/alerts?limit=20

# Pagination - page 2 (alertes 50-99)
curl http://localhost:8000/api/alerts?skip=50&limit=50

# Toutes les alertes non revues
curl http://localhost:8000/api/alerts?limit=1000 | jq '.[] | select(.reviewed == false)'
```

---

### PATCH /api/alerts/{alert_id}/review

Marque une alerte comme vérifiée et ajoute des notes.

**Request :**
```http
PATCH /api/alerts/1/review HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "notes": "Fausse alerte - jeu entre enfants"
}
```

**Query Parameters :**
| Paramètre | Type | Requis | Description |
|-----------|------|--------|-------------|
| `notes` | string | ❌ | Notes sur la révision de l'alerte |

**Response :**
```json
{
  "detail": "Marqué comme vérifié"
}
```

**Codes de statut :**
- `200 OK` : Alerte mise à jour
- `404 Not Found` : Alerte introuvable
- `500 Internal Server Error` : Erreur serveur

**Exemples cURL :**

```bash
# Marquer comme vérifié avec notes
curl -X PATCH "http://localhost:8000/api/alerts/1/review?notes=Incident%20confirmé"

# Marquer comme vérifié sans notes
curl -X PATCH http://localhost:8000/api/alerts/1/review
```

---

## 🎥 WebSocket - Streaming temps réel

### WS /ws/camera/{camera_id}

Flux WebSocket pour recevoir les frames annotées en temps réel.

**Connection :**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/camera/1');

ws.onopen = () => {
  console.log('Connecté au flux de la caméra 1');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // Structure du message
  console.log(data);
  /*
  {
    "camera_id": 1,
    "timestamp": "2024-01-15T14:32:10.123456",
    "frame": "base64_encoded_jpeg_image",
    "detection": {
      "label": "Violence",
      "confidence": 0.89,
      "trigger_alert": true
    },
    "metadata": {
      "fps": 30,
      "frame_number": 1234,
      "persons_detected": 2
    }
  }
  */
  
  // Afficher l'image
  const img = document.getElementById('camera-feed');
  img.src = 'data:image/jpeg;base64,' + data.frame;
  
  // Afficher le statut
  const status = document.getElementById('status');
  status.textContent = `${data.detection.label} (${(data.detection.confidence * 100).toFixed(1)}%)`;
  
  // Gérer les alertes
  if (data.detection.trigger_alert) {
    showAlert(data);
  }
};

ws.onerror = (error) => {
  console.error('Erreur WebSocket:', error);
};

ws.onclose = () => {
  console.log('Déconnecté du flux');
  // Tentative de reconnexion
  setTimeout(() => {
    connectCamera(1);
  }, 3000);
};
```

**Message Schema :**

```typescript
interface WebSocketMessage {
  camera_id: number;
  timestamp: string;  // ISO 8601 format
  frame: string;      // Base64 encoded JPEG
  detection: {
    label: "Violence" | "Normal";
    confidence: number;  // 0.0 - 1.0
    trigger_alert: boolean;
  };
  metadata: {
    fps: number;
    frame_number: number;
    persons_detected: number;
  };
}
```

**Exemple complet React :**

```jsx
import React, { useEffect, useRef, useState } from 'react';

function CameraFeed({ cameraId }) {
  const [status, setStatus] = useState('Connecting...');
  const [confidence, setConfidence] = useState(0);
  const wsRef = useRef(null);
  const imgRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/camera/${cameraId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('Connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Update image
      if (imgRef.current && data.frame) {
        imgRef.current.src = `data:image/jpeg;base64,${data.frame}`;
      }
      
      // Update status
      setStatus(data.detection.label);
      setConfidence(data.detection.confidence);
      
      // Alert handling
      if (data.detection.trigger_alert) {
        console.warn('Violence detected!', data);
        // Trigger notification, sound, etc.
      }
    };

    ws.onerror = (error) => {
      setStatus('Error');
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      setStatus('Disconnected');
      // Reconnect after 3 seconds
      setTimeout(() => {
        // Reconnect logic
      }, 3000);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [cameraId]);

  return (
    <div className="camera-feed">
      <img ref={imgRef} alt={`Camera ${cameraId}`} />
      <div className="overlay">
        <span className={status === 'Violence' ? 'alert' : 'normal'}>
          {status} ({(confidence * 100).toFixed(1)}%)
        </span>
      </div>
    </div>
  );
}
```

---

## 📁 Fichiers statiques

### GET /recordings/{filename}

Télécharge un enregistrement vidéo ou une miniature.

**Request :**
```http
GET /recordings/camera_1_20240115_143210.mp4 HTTP/1.1
Host: localhost:8000
```

**Response :**
- Type de contenu : `video/mp4` ou `image/jpeg`
- Corps : Données binaires du fichier

**Codes de statut :**
- `200 OK` : Fichier trouvé
- `404 Not Found` : Fichier introuvable

**Exemples :**

```bash
# Télécharger une vidéo
curl -O http://localhost:8000/recordings/camera_1_20240115_143210.mp4

# Télécharger une miniature
curl -O http://localhost:8000/recordings/camera_1_20240115_143210_thumb.jpg

# Lire directement dans le navigateur
# http://localhost:8000/recordings/camera_1_20240115_143210.mp4
```

**Structure des fichiers :**
```
recordings/
├── camera_{id}_{timestamp}.mp4       # Vidéo complète
└── camera_{id}_{timestamp}_thumb.jpg # Miniature
```

**Format du timestamp :** `YYYYMMDD_HHMMSS`

---

## 🔄 Codes de statut HTTP

| Code | Description | Usage |
|------|-------------|-------|
| `200` | OK | Requête réussie |
| `201` | Created | Ressource créée |
| `204` | No Content | Succès sans corps de réponse |
| `400` | Bad Request | Requête mal formée |
| `404` | Not Found | Ressource introuvable |
| `422` | Unprocessable Entity | Validation échouée |
| `500` | Internal Server Error | Erreur serveur |
| `503` | Service Unavailable | Service temporairement indisponible |

---

## 🧪 Exemples complets

### Python Client

```python
import requests
import json

class ViolenceSurveillanceClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_cameras(self):
        """Récupère toutes les caméras"""
        response = requests.get(f"{self.base_url}/api/cameras")
        response.raise_for_status()
        return response.json()
    
    def add_camera(self, name, url, location=""):
        """Ajoute une nouvelle caméra"""
        data = {"name": name, "url": url, "location": location}
        response = requests.post(
            f"{self.base_url}/api/cameras",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def delete_camera(self, camera_id):
        """Supprime une caméra"""
        response = requests.delete(
            f"{self.base_url}/api/cameras/{camera_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def toggle_camera(self, camera_id):
        """Active/désactive une caméra"""
        response = requests.patch(
            f"{self.base_url}/api/cameras/{camera_id}/toggle"
        )
        response.raise_for_status()
        return response.json()
    
    def get_alerts(self, skip=0, limit=50):
        """Récupère les alertes"""
        response = requests.get(
            f"{self.base_url}/api/alerts",
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
    
    def review_alert(self, alert_id, notes=""):
        """Marque une alerte comme vérifiée"""
        response = requests.patch(
            f"{self.base_url}/api/alerts/{alert_id}/review",
            params={"notes": notes}
        )
        response.raise_for_status()
        return response.json()

# Utilisation
client = ViolenceSurveillanceClient()

# Lister les caméras
cameras = client.get_cameras()
print(f"Caméras actives: {len(cameras)}")

# Ajouter une caméra
new_cam = client.add_camera(
    name="Caméra test",
    url="rtsp://192.168.1.100:554/stream",
    location="Bureau"
)
print(f"Caméra ajoutée avec ID: {new_cam['id']}")

# Récupérer les alertes non revues
alerts = client.get_alerts(limit=100)
unreviewed = [a for a in alerts if not a['reviewed']]
print(f"Alertes non revues: {len(unreviewed)}")

# Marquer une alerte comme vérifiée
if unreviewed:
    client.review_alert(
        unreviewed[0]['id'],
        notes="Incident confirmé"
    )
```

### JavaScript/TypeScript Client

```typescript
// api-client.ts
interface Camera {
  id: number;
  name: string;
  location: string;
  url: string;
  is_active: boolean;
}

interface Alert {
  id: number;
  camera_id: number;
  camera_name: string;
  confidence: number;
  detected_at: string;
  clip_path: string;
  thumbnail_path: string;
  reviewed: boolean;
  notes: string;
}

class ViolenceSurveillanceAPI {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async getCameras(): Promise<Camera[]> {
    const response = await fetch(`${this.baseUrl}/api/cameras`);
    if (!response.ok) throw new Error('Failed to fetch cameras');
    return response.json();
  }

  async addCamera(name: string, url: string, location: string = ''): Promise<Camera> {
    const response = await fetch(`${this.baseUrl}/api/cameras`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, url, location }),
    });
    if (!response.ok) throw new Error('Failed to add camera');
    return response.json();
  }

  async deleteCamera(cameraId: number): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/cameras/${cameraId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete camera');
  }

  async toggleCamera(cameraId: number): Promise<{ is_active: boolean }> {
    const response = await fetch(`${this.baseUrl}/api/cameras/${cameraId}/toggle`, {
      method: 'PATCH',
    });
    if (!response.ok) throw new Error('Failed to toggle camera');
    return response.json();
  }

  async getAlerts(skip: number = 0, limit: number = 50): Promise<Alert[]> {
    const response = await fetch(
      `${this.baseUrl}/api/alerts?skip=${skip}&limit=${limit}`
    );
    if (!response.ok) throw new Error('Failed to fetch alerts');
    return response.json();
  }

  async reviewAlert(alertId: number, notes: string = ''): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/alerts/${alertId}/review?notes=${encodeURIComponent(notes)}`,
      { method: 'PATCH' }
    );
    if (!response.ok) throw new Error('Failed to review alert');
  }

  connectWebSocket(cameraId: number): WebSocket {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    return new WebSocket(`${wsUrl}/ws/camera/${cameraId}`);
  }
}

export default ViolenceSurveillanceAPI;
```

---

## 📊 Limites et quotas

| Ressource | Limite | Notes |
|-----------|--------|-------|
| Caméras simultanées | 10 | Ajustable selon hardware |
| Alertes par requête | 1000 | Paramètre `limit` |
| WebSocket connexions | 50 | Par serveur |
| Taille fichier upload | N/A | Pas d'upload direct |
| Taux de requêtes | Illimité | À implémenter en production |

---

## 🔧 Configuration avancée

### CORS

Configurer dans `.env` :
```env
CORS_ORIGINS=http://localhost:3000,https://votre-domaine.com
```

### Rate Limiting

À implémenter avec `slowapi` :
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/cameras")
@limiter.limit("100/minute")
async def list_cameras():
    # ...
```

---

## 📞 Support

Pour toute question sur l'API :
- 📖 [Documentation complète](https://github.com/votre-username/ai-violence-detection-system/wiki)
- 💬 [Discussions GitHub](https://github.com/votre-username/ai-violence-detection-system/discussions)
- 🐛 [Signaler un bug](https://github.com/votre-username/ai-violence-detection-system/issues)
