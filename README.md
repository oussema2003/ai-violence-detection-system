# Détection de violence par vidéosurveillance

Un système qui regarde des flux de caméras de sécurité et prévient quand il repère une scène de violence. Au lieu d'analyser les images directement, il détecte d'abord les poses des personnes, puis un modèle de type Transformer analyse comment ces poses évoluent dans le temps pour décider si une scène est violente ou non.

Ce projet est un outil d'aide à la décision : une alerte doit toujours être vérifiée par une personne.

## Ce qu'il fait

- Analyse plusieurs caméras en même temps (RTSP, HTTP ou fichiers vidéo)
- Affiche les flux en direct dans une interface web
- Déclenche une alerte quand le score de violence dépasse un seuil réglable
- Enregistre automatiquement un clip de l'incident, quelques secondes avant et après
- Garde l'historique des alertes, avec la possibilité de les marquer comme vérifiées et d'ajouter des notes

## Comment ça marche

1. YOLOv8 Pose détecte les personnes et leurs points du corps sur chaque image.
2. Ces points sont transformés en un petit vecteur de caractéristiques par image.
3. Les 30 dernières images sont regroupées en une séquence.
4. Un Transformer classe la séquence : violence ou non.
5. Si le score dépasse le seuil (0,7 par défaut), une alerte est créée et le clip est enregistré.

## Technologies

- **IA** : PyTorch, Ultralytics YOLOv8 Pose, OpenCV
- **Backend** : FastAPI, SQLAlchemy, PostgreSQL
- **Frontend** : React, Vite
- **Déploiement** : Docker et Docker Compose

## Installation

Il faut Python 3.8 ou plus, Node.js 16 ou plus, et Docker si vous voulez tout lancer d'un coup. Une carte graphique NVIDIA est recommandée mais pas obligatoire.

**Avec Docker (le plus simple)**

```bash
git clone https://github.com/oussema2003/violence-surveillance-system.git
cd violence-surveillance-system/violence-surveillance
cp .env.example .env     # puis adaptez les variables
docker-compose up -d
```

**À la main**

```bash
# Backend
cd violence-surveillance/backend
python -m venv venv
source venv/bin/activate          # sous Windows : venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend, dans un autre terminal
cd violence-surveillance/frontend
npm install
npm run dev
```

Placez ensuite vos deux modèles dans `backend/models/` : le modèle YOLO de pose et le modèle `violence_transformer.pt` que vous avez entraîné.

## Réglages principaux

Ils se trouvent dans le fichier `.env` :

| Variable | Rôle | Par défaut |
|----------|------|------------|
| `VIOLENCE_THRESHOLD` | Seuil de détection. Plus haut = moins de fausses alertes, mais plus de cas manqués | 0.7 |
| `SEQUENCE_LENGTH` | Nombre d'images analysées ensemble | 30 |
| `WINDOW_STRIDE` | Fréquence d'analyse, en images | 10 |
| `PRE_ALERT_SECONDS` | Secondes enregistrées avant l'alerte | 5 |
| `POST_ALERT_SECONDS` | Secondes enregistrées après l'alerte | 10 |

## Utilisation

1. Ouvrez l'interface web (par défaut `http://localhost:3000`).
2. Dans la page Caméras, ajoutez un flux, par exemple `rtsp://utilisateur:motdepasse@192.168.1.100:554/stream`, ou un fichier vidéo pour tester.
3. Suivez les caméras sur le tableau de bord. Chaque flux affiche son état et son score de confiance.
4. Les alertes arrivent dans l'onglet Alertes, où vous pouvez regarder le clip, la vérifier et ajouter une note.

L'API est documentée automatiquement sur `/docs` une fois le backend lancé.

## Entraîner le modèle

Le dossier `Code d'entraînement/` contient tout ce qu'il faut. Il faut des vidéos classées en deux dossiers, `fight/` et `nonfight/`. Des jeux de données publics comme RWF-2000, Hockey Fight, Violent Flows ou RLVS peuvent servir de point de départ.

```bash
cd "Code d'entraînement"
python train.py --extract --max_frames 1000   # extraire les poses, une seule fois
python train.py --epochs 100                  # entraîner le Transformer
python evaluate.py                            # évaluer le modèle
```

Copiez ensuite `violence_transformer.pt` (et `scaler.pkl`) dans `backend/models/`.

## Résultats

Mesures obtenues pendant le développement sur mon jeu de validation. Elles donnent une idée de la qualité, mais ne remplacent pas un test sur vos propres caméras.

| Mesure | Score |
|--------|-------|
| Précision globale | 92,3 % |
| AUC-ROC | 0,942 |
| Precision | 87,5 % |
| Recall | 89,2 % |
| F1 | 88,3 % |

Sur une RTX 3080, le système tourne à environ 30 images par seconde. Sur CPU, comptez environ 8 images par seconde.

## Limites

- Les sports de combat, les danses énergiques et les jeux brusques entre enfants peuvent déclencher de fausses alertes.
- La violence hors champ, très masquée, mal éclairée ou filmée de très loin peut passer inaperçue.
- Le modèle ne comprend pas le contexte : il voit des mouvements, pas des intentions.
- Il faut protéger l'accès à l'API et respecter la réglementation sur la vidéosurveillance et la vie privée avant tout déploiement réel.

## Idées pour la suite

- Détection d'armes
- Analyse du son (cris, coups de feu)
- Suivi des personnes d'une image à l'autre
- Rapports automatiques et application mobile

## Auteur

Oussema Hidouri
[LinkedIn](https://www.linkedin.com/in/oussama-hidouri-6871932ab) | [GitHub](https://github.com/oussema2003) | oussemahidouri@gmail.com

Projet sous licence MIT.
