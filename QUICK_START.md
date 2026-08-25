# ⚡ Démarrage rapide

Guide ultra-rapide pour mettre en route le système de surveillance de violence en moins de 10 minutes.

## 🎯 Prérequis rapides

```bash
# Vérifiez que vous avez :
docker --version    # Docker 20+
docker-compose --version  # Docker Compose 2.0+
git --version       # Git 2.x
```

## 🚀 Installation en 5 étapes

### 1️⃣ Cloner le projet (30 secondes)

```bash
git clone https://github.com/votre-username/ai-violence-detection-system.git
cd ai-violence-detection-system
```

### 2️⃣ Configurer l'environnement (1 minute)

```bash
cd violence-surveillance
cp .env.example .env
```

**Windows :**
```cmd
notepad .env
```

**Linux/Mac :**
```bash
nano .env
```

**Changez uniquement cette ligne :**
```env
POSTGRES_PASSWORD=VotreMotDePasseSecurise123!
```

### 3️⃣ Télécharger les modèles (3 minutes)

Téléchargez les modèles pré-entraînés depuis [Releases](https://github.com/votre-username/ai-violence-detection-system/releases) et placez-les dans :

```
violence-surveillance/backend/models/
├── violence_transformer.pt
├── project_yolo26x-pose.pt
└── scaler.pkl
```

**OU** utilisez ce script rapide :

```bash
cd violence-surveillance/backend/models

# Linux/Mac
wget https://github.com/votre-username/ai-violence-detection-system/releases/download/v1.0.0/violence_transformer.pt
wget https://github.com/votre-username/ai-violence-detection-system/releases/download/v1.0.0/project_yolo26x-pose.pt
wget https://github.com/votre-username/ai-violence-detection-system/releases/download/v1.0.0/scaler.pkl

# Windows PowerShell
Invoke-WebRequest -Uri "https://github.com/votre-username/ai-violence-detection-system/releases/download/v1.0.0/violence_transformer.pt" -OutFile "violence_transformer.pt"
Invoke-WebRequest -Uri "https://github.com/votre-username/ai-violence-detection-system/releases/download/v1.0.0/project_yolo26x-pose.pt" -OutFile "project_yolo26x-pose.pt"
Invoke-WebRequest -Uri "https://github.com/votre-username/ai-violence-detection-system/releases/download/v1.0.0/scaler.pkl" -OutFile "scaler.pkl"
```

### 4️⃣ Lancer l'application (2 minutes)

```bash
cd violence-surveillance
docker-compose up -d
```

**Attendez que tous les services démarrent :**
```bash
docker-compose logs -f
# Ctrl+C pour quitter les logs
```

### 5️⃣ Accéder à l'interface (Immédiat)

Ouvrez votre navigateur : **http://localhost:3000**

🎉 **C'est prêt !**

---

## 📹 Ajouter votre première caméra

### Dans l'interface web

1. Cliquez sur **"Cameras"** dans le menu
2. Cliquez sur **"Add Camera"**
3. Remplissez :
   - **Name** : "Ma première caméra"
   - **Location** : "Bureau"
   - **URL** : Votre flux vidéo (voir exemples ci-dessous)
4. Cliquez **"Save"**

### Exemples d'URLs

**Caméra IP (RTSP) :**
```
rtsp://admin:password@192.168.1.100:554/stream
```

**Webcam HTTP :**
```
http://192.168.1.200:8080/video
```

**Fichier vidéo de test :**
```
/app/test_videos/sample.mp4
```

**Webcam locale (0 = première webcam) :**
```
0
```

### Avec l'API (cURL)

```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ma première caméra",
    "location": "Bureau",
    "url": "rtsp://192.168.1.100:554/stream"
  }'
```

---

## 🎥 Tester avec une vidéo

Si vous n'avez pas de caméra, testez avec une vidéo :

### 1. Préparer une vidéo de test

```bash
# Créer le dossier
mkdir -p violence-surveillance/backend/test_videos

# Copier votre vidéo
cp /chemin/vers/votre/video.mp4 violence-surveillance/backend/test_videos/
```

### 2. Ajouter comme "caméra"

```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vidéo de test",
    "url": "/app/test_videos/video.mp4"
  }'
```

### 3. Visualiser dans le dashboard

Allez sur http://localhost:3000 - votre vidéo s'affiche comme une caméra !

---

## 🔍 Vérifier que tout fonctionne

### Test 1 : Backend API

```bash
curl http://localhost:8000/api/cameras
# Devrait retourner la liste des caméras ([] si aucune)
```

### Test 2 : Documentation API

Ouvrez : http://localhost:8000/docs

### Test 3 : Frontend

Ouvrez : http://localhost:3000

### Test 4 : Logs

```bash
# Voir si des erreurs
docker-compose logs backend | grep ERROR

# Voir l'activité du backend
docker-compose logs -f backend
```

---

## ⚙️ Ajuster les paramètres (Optionnel)

### Seuil de détection

Éditez `.env` :
```env
# Plus haut = moins de faux positifs, mais peut manquer des incidents
VIOLENCE_THRESHOLD=0.7   # Par défaut

# Plus sensible (plus d'alertes)
VIOLENCE_THRESHOLD=0.6

# Moins sensible (moins de fausses alertes)
VIOLENCE_THRESHOLD=0.8
```

Puis redémarrez :
```bash
docker-compose restart backend
```

### Performance CPU/GPU

**Pour CPU uniquement :**
```env
DEVICE=cpu
SEQUENCE_LENGTH=20     # Au lieu de 30
WINDOW_STRIDE=15       # Au lieu de 10
```

**Pour GPU :**
```env
DEVICE=cuda
SEQUENCE_LENGTH=30
WINDOW_STRIDE=10
```

---

## 📊 Interface rapide

### Dashboard
- Vue multi-caméras en temps réel
- Statut de détection (Normal / Violence)
- Score de confiance

### Cameras
- Liste de toutes les caméras
- Ajouter / Supprimer / Activer-Désactiver
- Configuration individuelle

### Alerts
- Historique de toutes les alertes
- Vidéos enregistrées
- Miniatures
- Système de révision

---

## 🛑 Arrêter le système

```bash
cd violence-surveillance

# Arrêter sans supprimer les données
docker-compose stop

# Arrêter et supprimer les conteneurs
docker-compose down

# Arrêter et supprimer TOUT (données incluses)
docker-compose down -v
```

---

## 🆘 Problèmes courants

### "Port already in use"

**Problème :** Un service utilise déjà le port.

**Solution :**
```bash
# Changer les ports dans docker-compose.yml
# Ou arrêter le service en conflit
```

### "Cannot connect to database"

**Problème :** PostgreSQL n'est pas prêt.

**Solution :**
```bash
# Attendre 30 secondes puis :
docker-compose restart backend
```

### "Model not found"

**Problème :** Les modèles ne sont pas téléchargés.

**Solution :**
```bash
# Vérifier que les fichiers existent
ls violence-surveillance/backend/models/
# Devrait afficher : violence_transformer.pt, project_yolo26x-pose.pt, scaler.pkl
```

### Performance très lente

**Problème :** GPU non détecté ou CPU trop faible.

**Solution :**
```bash
# Vérifier GPU
docker-compose exec backend python -c "import torch; print(torch.cuda.is_available())"

# Si False, suivre le guide GPU
```

### "CUDA out of memory"

**Problème :** Pas assez de VRAM.

**Solution :** Éditez `.env`
```env
MAX_PERSONS_PER_FRAME=3   # Réduire de 10 à 3
```

---

## 📚 Prochaines étapes

Maintenant que tout fonctionne :

1. **📖 [Guide complet](README.md)** - Documentation détaillée
2. **📡 [Documentation API](docs/API.md)** - Intégrations personnalisées
3. **🔧 [Configuration avancée](docs/CONFIGURATION.md)** - Optimiser les performances
4. **🎓 [Entraîner votre modèle](docs/TRAINING.md)** - Personnaliser la détection
5. **🚀 [Déployer en production](docs/DEPLOYMENT.md)** - Mise en production

---

## 💬 Besoin d'aide ?

- 📖 [Documentation complète](https://github.com/votre-username/ai-violence-detection-system/wiki)
- 💬 [Forum de discussion](https://github.com/votre-username/ai-violence-detection-system/discussions)
- 🐛 [Signaler un bug](https://github.com/votre-username/ai-violence-detection-system/issues)
- 📧 Email : support@violence-surveillance.com

---

**🎉 Félicitations ! Vous êtes opérationnel en moins de 10 minutes !**
