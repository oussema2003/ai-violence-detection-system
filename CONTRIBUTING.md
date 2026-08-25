# 🤝 Guide de Contribution

Merci de votre intérêt pour contribuer au projet de Système de Surveillance de Violence par IA ! Ce document contient les directives pour contribuer efficacement.

## 📋 Table des matières

- [Code de conduite](#code-de-conduite)
- [Comment contribuer](#comment-contribuer)
- [Standards de code](#standards-de-code)
- [Processus de Pull Request](#processus-de-pull-request)
- [Signaler des bugs](#signaler-des-bugs)
- [Proposer des fonctionnalités](#proposer-des-fonctionnalités)
- [Structure des commits](#structure-des-commits)

## 📜 Code de conduite

Ce projet adhère aux principes de respect et d'inclusivité. En participant, vous acceptez de :

- Être respectueux et constructif dans vos interactions
- Accepter les critiques constructives
- Vous concentrer sur ce qui est le mieux pour la communauté
- Faire preuve d'empathie envers les autres membres

## 🚀 Comment contribuer

### 1. Fork et clone

```bash
# Fork le projet sur GitHub
# Ensuite clonez votre fork
git clone https://github.com/votre-username/ai-violence-detection-system.git
cd ai-violence-detection-system

# Ajoutez le dépôt original comme remote
git remote add upstream https://github.com/original-username/ai-violence-detection-system.git
```

### 2. Créer une branche

```bash
# Assurez-vous d'être à jour
git checkout main
git pull upstream main

# Créez une nouvelle branche
git checkout -b feature/ma-nouvelle-fonctionnalite
# ou
git checkout -b fix/correction-du-bug
```

### 3. Configurer l'environnement

```bash
# Backend
cd violence-surveillance/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend
cd ../frontend
npm install
```

### 4. Faire vos modifications

- Écrivez du code propre et lisible
- Suivez les standards de code (voir ci-dessous)
- Ajoutez des tests si applicable
- Mettez à jour la documentation si nécessaire

### 5. Tester vos modifications

```bash
# Backend - Tests unitaires
cd violence-surveillance/backend
pytest tests/

# Backend - Linting
flake8 .
black . --check
mypy .

# Frontend - Tests
cd ../frontend
npm test

# Frontend - Linting
npm run lint
```

### 6. Commit et push

```bash
git add .
git commit -m "feat: ajoute la fonctionnalité X"
git push origin feature/ma-nouvelle-fonctionnalite
```

### 7. Créer une Pull Request

- Allez sur votre fork GitHub
- Cliquez sur "New Pull Request"
- Remplissez le template de PR
- Attendez la revue de code

## 🎨 Standards de code

### Python (Backend)

#### Style de code

Nous suivons [PEP 8](https://pep8.org/) avec quelques adaptations :

```python
# Utilisez Black pour le formatage automatique
black . --line-length 100

# Flake8 pour le linting
flake8 . --max-line-length 100 --ignore E203,W503

# MyPy pour le type checking
mypy . --strict
```

#### Conventions de nommage

```python
# Variables et fonctions : snake_case
def calculate_violence_score(features: np.ndarray) -> float:
    violence_threshold = 0.7
    return score

# Classes : PascalCase
class ViolenceDetector:
    pass

# Constantes : UPPER_SNAKE_CASE
MAX_SEQUENCE_LENGTH = 30
DEFAULT_THRESHOLD = 0.7

# Méthodes privées : _prefixe
def _internal_method(self):
    pass
```

#### Docstrings

Utilisez le format Google :

```python
def process_frame(frame: np.ndarray, threshold: float = 0.7) -> dict:
    """
    Traite une frame vidéo pour détecter la violence.

    Args:
        frame: Image numpy array (H, W, C) en format BGR
        threshold: Seuil de confiance pour la détection (0.0-1.0)

    Returns:
        Dictionnaire contenant:
            - label: "Violence" ou "Normal"
            - confidence: score de confiance (0.0-1.0)
            - trigger_alert: booléen indiquant si alerte

    Raises:
        ValueError: Si frame est None ou vide
        RuntimeError: Si le modèle n'est pas chargé

    Example:
        >>> detector = ViolenceDetector()
        >>> frame = cv2.imread("test.jpg")
        >>> result = detector.process_frame(frame)
        >>> print(result["label"])
        "Normal"
    """
    pass
```

#### Structure des imports

```python
# 1. Standard library
import os
import sys
from typing import List, Dict, Optional

# 2. Third-party
import numpy as np
import torch
from fastapi import FastAPI

# 3. Local
from core.inference import ViolenceDetector
from db.models import Camera
```

### JavaScript/React (Frontend)

#### Style de code

```bash
# ESLint pour le linting
npm run lint

# Prettier pour le formatage
npm run format
```

#### Conventions de nommage

```javascript
// Variables et fonctions : camelCase
const videoFeedUrl = "http://localhost:8001";
function calculateConfidence(score) {
  return score * 100;
}

// Composants React : PascalCase
function VideoFeed({ cameraId }) {
  return <div>...</div>;
}

// Constantes : UPPER_SNAKE_CASE
const MAX_RECONNECT_ATTEMPTS = 5;
const DEFAULT_TIMEOUT = 3000;

// Fichiers de composants : PascalCase
// VideoFeed.jsx, AlertBadge.jsx

// Fichiers utilitaires : camelCase
// apiClient.js, videoUtils.js
```

#### Structure des composants

```javascript
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * Composant d'affichage du flux vidéo d'une caméra
 * @param {number} cameraId - ID de la caméra
 * @param {function} onAlert - Callback appelé lors d'une alerte
 */
function VideoFeed({ cameraId, onAlert }) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Setup
    return () => {
      // Cleanup
    };
  }, [cameraId]);

  if (error) return <div>Error: {error}</div>;
  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="video-feed">
      {/* JSX */}
    </div>
  );
}

VideoFeed.propTypes = {
  cameraId: PropTypes.number.isRequired,
  onAlert: PropTypes.func,
};

VideoFeed.defaultProps = {
  onAlert: () => {},
};

export default VideoFeed;
```

## 🔄 Processus de Pull Request

### Template de PR

Votre PR doit inclure :

```markdown
## Description
Brève description des changements

## Type de changement
- [ ] Bug fix (changement non-breaking qui corrige un bug)
- [ ] Nouvelle fonctionnalité (changement non-breaking qui ajoute une fonctionnalité)
- [ ] Breaking change (correction ou fonctionnalité qui causerait un dysfonctionnement de fonctionnalités existantes)
- [ ] Documentation

## Checklist
- [ ] Mon code suit les standards du projet
- [ ] J'ai effectué une auto-revue de mon code
- [ ] J'ai commenté mon code, particulièrement dans les zones complexes
- [ ] J'ai mis à jour la documentation
- [ ] Mes changements ne génèrent pas de nouveaux warnings
- [ ] J'ai ajouté des tests qui prouvent que ma correction est efficace ou que ma fonctionnalité fonctionne
- [ ] Les tests unitaires nouveaux et existants passent localement
- [ ] Toutes les dépendances requises ont été ajoutées

## Tests effectués
Décrivez les tests que vous avez effectués

## Screenshots (si applicable)
Ajoutez des screenshots pour illustrer les changements UI

## Contexte additionnel
Ajoutez tout autre contexte pertinent
```

### Processus de revue

1. **Revue automatique** : Les CI/CD checks doivent passer
2. **Revue par les pairs** : Au moins 1 approbation requise
3. **Tests** : Tous les tests doivent passer
4. **Documentation** : Documentation mise à jour si nécessaire
5. **Merge** : Squash and merge pour garder l'historique propre

## 🐛 Signaler des bugs

### Avant de signaler

- Vérifiez que le bug n'a pas déjà été signalé
- Assurez-vous d'utiliser la dernière version
- Essayez de reproduire le bug

### Template de bug report

```markdown
## Description du bug
Description claire et concise du bug

## Comment reproduire
Étapes pour reproduire le comportement:
1. Aller à '...'
2. Cliquer sur '...'
3. Scroller jusqu'à '...'
4. Voir l'erreur

## Comportement attendu
Description claire de ce qui devrait se passer

## Comportement actuel
Description de ce qui se passe actuellement

## Screenshots
Si applicable, ajoutez des screenshots

## Environnement
- OS: [ex: Windows 10, Ubuntu 22.04]
- Python: [ex: 3.9.5]
- PyTorch: [ex: 2.3.0]
- CUDA: [ex: 11.8]
- Navigateur: [ex: Chrome 120]

## Logs
```
Collez les logs d'erreur ici
```

## Contexte additionnel
Tout autre contexte pertinent
```

## 💡 Proposer des fonctionnalités

### Template de feature request

```markdown
## Problème à résoudre
Description claire du problème que cette fonctionnalité résoudrait

## Solution proposée
Description claire de ce que vous voulez qu'il se passe

## Alternatives considérées
Description des solutions alternatives que vous avez considérées

## Contexte additionnel
Screenshots, mockups, exemples de code, etc.

## Impact estimé
- [ ] Haute priorité
- [ ] Priorité moyenne
- [ ] Basse priorité

## Effort estimé
- [ ] Petit (< 1 jour)
- [ ] Moyen (1-3 jours)
- [ ] Grand (> 3 jours)
```

## 📝 Structure des commits

Nous suivons la convention [Conventional Commits](https://www.conventionalcommits.org/) :

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: Nouvelle fonctionnalité
- **fix**: Correction de bug
- **docs**: Documentation uniquement
- **style**: Changements de style (formatage, etc.)
- **refactor**: Refactorisation du code
- **perf**: Amélioration de performance
- **test**: Ajout ou modification de tests
- **chore**: Maintenance (dépendances, config, etc.)
- **ci**: Changements CI/CD

### Exemples

```bash
# Bons commits
git commit -m "feat(detector): ajoute la détection d'armes"
git commit -m "fix(api): corrige l'erreur de connexion WebSocket"
git commit -m "docs(readme): met à jour les instructions d'installation"
git commit -m "refactor(transformer): simplifie la logique d'attention"
git commit -m "perf(inference): optimise l'extraction de features"

# Avec body et footer
git commit -m "feat(alerts): ajoute l'export PDF des alertes

- Génération PDF avec reportlab
- Template personnalisable
- Export par période

Closes #123"
```

### Scope

Les scopes courants :

**Backend:**
- `api` : Endpoints REST
- `detector` : Pipeline de détection
- `transformer` : Modèle Transformer
- `yolo` : YOLOv8 integration
- `camera` : Gestion caméras
- `alerts` : Système d'alertes
- `db` : Base de données
- `recorder` : Enregistrement vidéo

**Frontend:**
- `ui` : Interface utilisateur
- `dashboard` : Dashboard
- `camera-view` : Vue caméras
- `alerts-panel` : Panneau alertes
- `config` : Configuration

**Général:**
- `docs` : Documentation
- `tests` : Tests
- `ci` : CI/CD
- `deps` : Dépendances

## 🎯 Domaines de contribution

Nous accueillons les contributions dans ces domaines :

### 🔴 Haute priorité

- [ ] Tests unitaires et d'intégration
- [ ] Optimisation des performances
- [ ] Documentation API
- [ ] Correction de bugs critiques
- [ ] Support multi-langues (i18n)

### 🟡 Priorité moyenne

- [ ] Nouvelles fonctionnalités (voir roadmap)
- [ ] Amélioration UI/UX
- [ ] Exemples et tutoriels
- [ ] Refactorisation du code
- [ ] Amélioration de la CI/CD

### 🟢 Basse priorité

- [ ] Optimisations mineures
- [ ] Améliorations cosmétiques
- [ ] Documentation supplémentaire
- [ ] Exemples additionnels

## 📚 Ressources utiles

### Documentation technique

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [React Documentation](https://react.dev/)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)

### Standards et guides

- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [Conventional Commits](https://www.conventionalcommits.org/)

### Outils

- [Black - Code formatter](https://black.readthedocs.io/)
- [Flake8 - Linter](https://flake8.pycqa.org/)
- [MyPy - Type checker](https://mypy.readthedocs.io/)
- [ESLint - JavaScript linter](https://eslint.org/)
- [Prettier - Code formatter](https://prettier.io/)

## ❓ Questions

Si vous avez des questions, n'hésitez pas à :

- Ouvrir une [Discussion GitHub](https://github.com/username/repo/discussions)
- Rejoindre notre [Discord](https://discord.gg/your-server)
- Envoyer un email à support@violence-surveillance.com

## 🙏 Remerciements

Merci à tous les contributeurs qui aident à améliorer ce projet !

---

**Merci de contribuer ! Ensemble, rendons les espaces publics plus sûrs. 🛡️**
