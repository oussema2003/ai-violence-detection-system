# 📦 Guide d'installation détaillé

Ce guide vous accompagne pas à pas pour installer et configurer le système de surveillance de violence par IA.

## 📋 Table des matières

- [Prérequis](#prérequis)
- [Installation rapide avec Docker](#installation-rapide-avec-docker)
- [Installation locale pour développement](#installation-locale-pour-développement)
- [Configuration GPU NVIDIA](#configuration-gpu-nvidia)
- [Vérification de l'installation](#vérification-de-linstallation)
- [Dépannage](#dépannage)

## 🔧 Prérequis

### Système d'exploitation

- ✅ **Linux** : Ubuntu 20.04+, Debian 11+, CentOS 8+
- ✅ **Windows** : Windows 10/11 avec WSL2
- ✅ **macOS** : macOS 11+ (M1/M2 supporté en mode CPU)

### Logiciels requis

#### Obligatoires

```bash
# Vérifier les versions installées
python --version    # Python 3.8 ou supérieur
node --version      # Node.js 16 ou supérieur
npm --version       # npm 8 ou supérieur
git --version       # Git 2.x
docker --version    # Docker 20.x ou supérieur (pour Docker)
```

#### Recommandés

- **Docker Compose** v2.0+ (pour déploiement facile)
- **GPU NVIDIA** avec CUDA 11.8+ (pour meilleures performances)
- **PostgreSQL** 15+ (ou utilisez Docker)

### Configuration matérielle minimale

#### CPU seulement (Développement/Test)
- **CPU** : 4 cœurs minimum (8 recommandés)
- **RAM** : 8 GB minimum (16 GB recommandés)
- **Stockage** : 20 GB disponible
- **Performance** : ~8-15 FPS

#### Avec GPU (Production)
- **CPU** : 4 cœurs minimum
- **RAM** : 16 GB minimum (32 GB pour multi-caméras)
- **GPU** : NVIDIA GTX 1660 ou supérieur (RTX 3060+ recommandé)
- **VRAM** : 6 GB minimum (8+ GB recommandé)
- **Stockage** : 50 GB disponible (SSD recommandé)
- **Performance** : ~25-30 FPS

## 🐳 Installation rapide avec Docker

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-username/ai-violence-detection-system.git
cd ai-violence-detection-system
```

### 2. Configurer les variables d'environnement

```bash
cd violence-surveillance
cp .env.example .env
```

Éditez le fichier `.env` avec vos paramètres :

```bash
# Windows
notepad .env

# Linux/Mac
nano .env
# ou
vim .env
```

**Changements minimums requis :**
```env
POSTGRES_PASSWORD=VotreMotDePasseSecurise123!
DATABASE_URL=postgresql://surveillance:VotreMotDePasseSecurise123!@db:5432/surveillance
```

### 3. Télécharger les modèles

Les modèles pré-entraînés doivent être placés dans `violence-surveillance/backend/models/` :

```bash
mkdir -p violence-surveillance/backend/models
cd violence-surveillance/backend/models
```

**Téléchargez :**
1. `violence_transformer.pt` - Modèle Transformer entraîné
2. `project_yolo26x-pose.pt` - Modèle YOLOv8-Pose
3. `scaler.pkl` - Normaliseur de features

> 📥 Liens de téléchargement : [Releases](https://github.com/votre-username/ai-violence-detection-system/releases)

### 4. Lancer avec Docker Compose

```bash
cd violence-surveillance

# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Vérifier que tous les services sont running
docker-compose ps
```

**Services démarrés :**
- `db` : PostgreSQL (port 5432)
- `backend` : FastAPI (port 8001)
- `frontend` : React (port 3000)
- `nginx` : Reverse proxy (port 8080)

### 5. Accéder à l'application

Ouvrez votre navigateur :
- **Interface principale** : http://localhost:3000
- **API Documentation** : http://localhost:8001/docs
- **Nginx (reverse proxy)** : http://localhost:8080

## 💻 Installation locale pour développement

### Backend Python

#### 1. Naviguer vers le backend

```bash
cd violence-surveillance/backend
```

#### 2. Créer un environnement virtuel

**Windows :**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac :**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Installer les dépendances

**Pour GPU (NVIDIA CUDA) :**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Pour CPU uniquement :**
```bash
pip install --upgrade pip
pip install -r requirements_simple.txt
```

#### 4. Configurer la base de données

**Option A : PostgreSQL avec Docker**
```bash
docker run -d \
  --name violence-db \
  -e POSTGRES_USER=surveillance \
  -e POSTGRES_PASSWORD=yourpassword \
  -e POSTGRES_DB=surveillance \
  -p 5432:5432 \
  postgres:15
```

**Option B : SQLite (développement simple)**

Éditez `.env` :
```env
DATABASE_URL=sqlite:///./data/surveillance.db
```

#### 5. Initialiser la base de données

```bash
python -c "from db.database import init_db; init_db()"
```

#### 6. Placer les modèles

Copiez les modèles dans `backend/models/` :
```
backend/models/
├── violence_transformer.pt
├── project_yolo26x-pose.pt
└── scaler.pkl
```

#### 7. Lancer le backend

```bash
# Mode développement avec auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Mode production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

Le backend est accessible sur : http://localhost:8000

### Frontend React

#### 1. Naviguer vers le frontend

```bash
cd violence-surveillance/frontend
```

#### 2. Installer les dépendances

```bash
npm install
```

#### 3. Configurer l'URL de l'API

Créez `.env.local` :
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

#### 4. Lancer le serveur de développement

```bash
npm run dev
```

Le frontend est accessible sur : http://localhost:3000

#### 5. Build de production (optionnel)

```bash
npm run build

# Prévisualiser le build
npm run preview
```

## 🎮 Configuration GPU NVIDIA

### Vérifier la disponibilité CUDA

```bash
# Vérifier NVIDIA driver
nvidia-smi

# Vérifier CUDA dans Python
python -c "import torch; print(f'CUDA disponible: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

### Installer CUDA Toolkit

**Windows :**
1. Télécharger CUDA Toolkit : https://developer.nvidia.com/cuda-downloads
2. Installer avec les options par défaut
3. Redémarrer le système

**Linux (Ubuntu/Debian) :**
```bash
# CUDA 11.8
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda-repo-ubuntu2204-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-11-8-local_11.8.0-520.61.05-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2204-11-8-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda
```

### Configuration Docker avec GPU

#### 1. Installer NVIDIA Container Toolkit

**Linux :**
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

#### 2. Tester Docker avec GPU

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

#### 3. Activer GPU dans docker-compose.yml

Décommentez la section GPU :
```yaml
backend:
  # ...
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

## ✅ Vérification de l'installation

### Script de vérification automatique

Créez `check_installation.py` :

```python
#!/usr/bin/env python3
import sys

def check_python():
    version = sys.version_info
    if version >= (3, 8):
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} (3.8+ requis)")
        return False

def check_packages():
    packages = {
        'torch': 'PyTorch',
        'cv2': 'OpenCV',
        'fastapi': 'FastAPI',
        'ultralytics': 'Ultralytics',
        'sqlalchemy': 'SQLAlchemy',
    }
    
    all_ok = True
    for pkg, name in packages.items():
        try:
            __import__(pkg)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} manquant")
            all_ok = False
    return all_ok

def check_cuda():
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA disponible - {torch.cuda.get_device_name(0)}")
            print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            return True
        else:
            print("⚠️  CUDA non disponible (mode CPU)")
            return False
    except:
        print("❌ Impossible de vérifier CUDA")
        return False

def check_models():
    import os
    models = [
        'backend/models/violence_transformer.pt',
        'backend/models/project_yolo26x-pose.pt',
        'backend/models/scaler.pkl',
    ]
    
    all_ok = True
    for model in models:
        if os.path.exists(model):
            size = os.path.getsize(model) / 1e6
            print(f"✅ {model} ({size:.1f} MB)")
        else:
            print(f"❌ {model} manquant")
            all_ok = False
    return all_ok

if __name__ == "__main__":
    print("🔍 Vérification de l'installation\n")
    
    checks = [
        check_python(),
        check_packages(),
        check_cuda(),
        check_models(),
    ]
    
    print("\n" + "="*50)
    if all(checks):
        print("✅ Installation complète et fonctionnelle!")
    else:
        print("⚠️  Certains composants sont manquants")
        print("   Consultez le guide d'installation pour résoudre les problèmes")
```

Exécutez :
```bash
python check_installation.py
```

### Tests manuels

#### 1. Test du backend

```bash
cd violence-surveillance/backend

# Test d'import des modules
python -c "from core.inference import ViolenceDetector; print('✅ Backend OK')"

# Test du serveur API
curl http://localhost:8000/api/cameras
```

#### 2. Test du frontend

```bash
cd violence-surveillance/frontend

# Vérifier le build
npm run build
```

#### 3. Test complet avec vidéo

```bash
cd violence-surveillance/backend
python test_video.py --video /chemin/vers/video.mp4
```

## 🔧 Dépannage

### Problèmes courants

#### Erreur : "CUDA out of memory"

**Solution :**
```env
# Dans .env
BATCH_SIZE=1
MAX_PERSONS_PER_FRAME=5
```

#### Erreur : "Module not found"

**Solution :**
```bash
# Vérifier l'environnement virtuel est activé
pip install -r requirements.txt --force-reinstall
```

#### Erreur : "Connection refused" (PostgreSQL)

**Solution :**
```bash
# Vérifier que PostgreSQL est démarré
docker ps | grep postgres

# Redémarrer si nécessaire
docker restart violence-db
```

#### Performance lente (CPU)

**Solution :**
```env
# Réduire la résolution
CAMERA_RESOLUTION=640x480

# Augmenter le stride
WINDOW_STRIDE=15

# Réduire le nombre de personnes trackées
MAX_PERSONS_PER_FRAME=3
```

#### Erreur : "YOLOv8 model not found"

**Solution :**
```bash
# Télécharger manuellement le modèle
cd backend/models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8x-pose.pt
```

### Logs de débogage

#### Docker

```bash
# Logs de tous les services
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f backend

# Logs avec timestamps
docker-compose logs -f --timestamps
```

#### Backend local

```bash
# Activer le mode debug
export DEBUG=true
uvicorn main:app --reload --log-level debug
```

#### Frontend local

```bash
# Mode verbose
npm run dev -- --debug
```

### Support

Si vous rencontrez d'autres problèmes :

1. 📖 Consultez la [FAQ](https://github.com/votre-username/ai-violence-detection-system/wiki/FAQ)
2. 🐛 Ouvrez une [issue GitHub](https://github.com/votre-username/ai-violence-detection-system/issues)
3. 💬 Rejoignez notre [Discord](https://discord.gg/your-server)
4. 📧 Email : support@violence-surveillance.com

## ✅ Prochaines étapes

Une fois l'installation réussie :

1. 📹 [Configurer vos caméras](CAMERA_SETUP.md)
2. ⚙️ [Ajuster les paramètres de détection](CONFIGURATION.md)
3. 🎓 [Entraîner votre propre modèle](TRAINING.md) (optionnel)
4. 🚀 [Déployer en production](DEPLOYMENT.md)

---

**Besoin d'aide ?** N'hésitez pas à demander sur notre [forum de support](https://github.com/votre-username/ai-violence-detection-system/discussions) ! 🙌
