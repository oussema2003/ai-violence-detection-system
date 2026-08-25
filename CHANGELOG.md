# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

### À venir
- Support multi-langues (EN, FR, ES, AR)
- Détection d'armes blanches et à feu
- Analyse audio des incidents
- Application mobile (iOS/Android)
- Export de rapports PDF/Excel

## [1.0.0] - 2024-12-XX

### 🎉 Version initiale

#### Ajouté
- **Modèle de détection IA**
  - Architecture hybride YOLOv8-Pose + Transformer
  - Détection de 26 keypoints humains
  - Classification temporelle sur 30 frames
  - Précision de 92.3% (AUC: 0.942)

- **Backend FastAPI**
  - API REST complète pour gestion caméras et alertes
  - WebSocket pour streaming temps réel
  - Pipeline d'inférence multi-caméras
  - Enregistrement automatique des incidents
  - Base de données PostgreSQL/SQLite

- **Frontend React**
  - Dashboard multi-caméras responsive
  - Visualisation temps réel des flux vidéo
  - Panneau de gestion des alertes
  - Interface de configuration des caméras
  - Lecture des enregistrements d'incidents

- **Système d'alertes**
  - Détection temps réel avec seuil configurable
  - Enregistrement pré/post-événement
  - Génération automatique de miniatures
  - Historique complet avec système de révision
  - Notification instantanée via WebSocket

- **Infrastructure**
  - Docker Compose pour déploiement facile
  - Configuration Nginx pour reverse proxy
  - Support GPU NVIDIA avec CUDA
  - Variables d'environnement configurables

- **Documentation**
  - README détaillé en français
  - Guide d'installation complet
  - Documentation API (Swagger/ReDoc)
  - Guide de contribution
  - Exemples d'utilisation

#### Code d'entraînement
- Script d'entraînement avec augmentation avancée
  - Mixup et CutMix temporel
  - Gradient accumulation
  - Cosine Annealing LR avec warmup
  - Label smoothing
  - Test Time Augmentation (TTA)

- Outils d'évaluation
  - Métriques complètes (Accuracy, AUC, Precision, Recall)
  - Visualisation des résultats
  - Test sur vidéos
  - Export des courbes d'apprentissage

#### Performances
- 30 FPS sur GPU RTX 3080
- Latence < 50ms pour la détection
- Support de caméras multiples simultanées
- Gestion automatique de la mémoire GPU

### Technique
- Python 3.8+ avec PyTorch 2.3.0
- FastAPI 0.111.0 pour l'API
- React 18.2.0 pour le frontend
- YOLOv8x-Pose pour la détection
- PostgreSQL 15 pour la persistance

## Types de changements

- **Added** (Ajouté) : pour les nouvelles fonctionnalités
- **Changed** (Modifié) : pour les changements aux fonctionnalités existantes
- **Deprecated** (Déprécié) : pour les fonctionnalités bientôt supprimées
- **Removed** (Supprimé) : pour les fonctionnalités supprimées
- **Fixed** (Corrigé) : pour les corrections de bugs
- **Security** (Sécurité) : en cas de vulnérabilités

---

## Template pour futures versions

## [X.Y.Z] - YYYY-MM-DD

### Added
- Nouvelle fonctionnalité A
- Nouvelle fonctionnalité B

### Changed
- Modification de la fonctionnalité C
- Amélioration de D

### Deprecated
- Fonctionnalité E sera supprimée dans v2.0.0

### Removed
- Suppression de la fonctionnalité F

### Fixed
- Correction du bug #123
- Correction du bug #456

### Security
- Correction de la vulnérabilité CVE-XXXX

---

[Unreleased]: https://github.com/votre-username/ai-violence-detection-system/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/votre-username/ai-violence-detection-system/releases/tag/v1.0.0
