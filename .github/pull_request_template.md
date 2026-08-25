## 📝 Description

<!-- Décrivez vos changements en détail -->

## 🎯 Type de changement

<!-- Cochez les cases appropriées -->

- [ ] 🐛 Bug fix (changement non-breaking qui corrige un bug)
- [ ] ✨ Nouvelle fonctionnalité (changement non-breaking qui ajoute une fonctionnalité)
- [ ] 💥 Breaking change (correction ou fonctionnalité qui causerait un dysfonctionnement de fonctionnalités existantes)
- [ ] 📚 Documentation (mise à jour de la documentation uniquement)
- [ ] 🎨 Style (formatage, point-virgules manquants, etc. ; pas de changement de code)
- [ ] ♻️ Refactoring (ni correction de bug ni ajout de fonctionnalité)
- [ ] ⚡ Performance (amélioration des performances)
- [ ] ✅ Tests (ajout de tests manquants ou correction de tests existants)
- [ ] 🔧 Chore (changements du processus de build ou outils auxiliaires)

## 🔗 Issues liées

<!-- Référencez les issues liées -->

Closes #(issue)
Fixes #(issue)
Related to #(issue)

## 📋 Checklist

### Code Quality

- [ ] Mon code suit les standards de style du projet
- [ ] J'ai effectué une auto-revue de mon code
- [ ] J'ai commenté mon code, particulièrement dans les zones difficiles à comprendre
- [ ] J'ai fait les changements correspondants dans la documentation

### Testing

- [ ] Mes changements ne génèrent pas de nouveaux warnings
- [ ] J'ai ajouté des tests qui prouvent que ma correction est efficace ou que ma fonctionnalité fonctionne
- [ ] Les tests unitaires nouveaux et existants passent localement avec mes changements
- [ ] J'ai testé manuellement les changements

### Documentation

- [ ] J'ai mis à jour le README si nécessaire
- [ ] J'ai mis à jour la documentation API si nécessaire
- [ ] J'ai ajouté des docstrings aux nouvelles fonctions/classes
- [ ] J'ai mis à jour le CHANGELOG.md

### Dependencies

- [ ] J'ai vérifié que toutes les nouvelles dépendances sont nécessaires
- [ ] J'ai mis à jour requirements.txt / package.json
- [ ] Les versions des dépendances sont fixées

## 🧪 Tests effectués

<!-- Décrivez les tests que vous avez effectués pour vérifier vos changements -->

### Backend Tests

```bash
# Commandes de test exécutées
pytest tests/ -v
```

### Frontend Tests

```bash
# Commandes de test exécutées
npm test
```

### Tests manuels

- [ ] Testé avec GPU NVIDIA
- [ ] Testé en mode CPU
- [ ] Testé avec Docker
- [ ] Testé en développement local
- [ ] Testé sur différents navigateurs (si frontend)

**Environnement de test :**
- OS: 
- Python: 
- PyTorch: 
- CUDA: 
- Navigateur: 

## 📸 Screenshots / Vidéos

<!-- Si applicable, ajoutez des screenshots ou vidéos pour illustrer les changements UI -->

### Avant
<!-- Screenshot de l'état avant les changements -->

### Après
<!-- Screenshot de l'état après les changements -->

## 🔍 Code Review Checklist

<!-- Pour les reviewers -->

- [ ] Le code est clair et facile à comprendre
- [ ] Les noms de variables/fonctions sont descriptifs
- [ ] Pas de code dupliqué
- [ ] Les erreurs sont gérées correctement
- [ ] Les logs sont appropriés
- [ ] Pas de secrets/credentials hardcodés
- [ ] Performance acceptable
- [ ] Sécurité respectée

## 📊 Impact sur les performances

<!-- Si applicable, décrivez l'impact sur les performances -->

- [ ] Aucun impact sur les performances
- [ ] Amélioration des performances : ______
- [ ] Légère dégradation acceptable : ______
- [ ] Tests de performance effectués

**Métriques (si applicable) :**
- FPS avant/après : 
- Latence avant/après : 
- Utilisation mémoire avant/après : 

## 🔒 Considérations de sécurité

<!-- Y a-t-il des implications de sécurité ? -->

- [ ] Aucune implication de sécurité
- [ ] J'ai vérifié les vulnérabilités potentielles
- [ ] J'ai validé toutes les entrées utilisateur
- [ ] J'ai utilisé des requêtes paramétrées pour la DB
- [ ] Pas de données sensibles dans les logs

## 🚀 Déploiement

<!-- Instructions spéciales pour le déploiement -->

### Migrations nécessaires

- [ ] Migration de base de données requise
- [ ] Changement de configuration requis
- [ ] Mise à jour des variables d'environnement
- [ ] Redémarrage de service requis

### Instructions de déploiement

```bash
# Commandes spéciales à exécuter
```

## ℹ️ Contexte additionnel

<!-- Ajoutez tout autre contexte sur la PR ici -->

## 👥 Mentions

<!-- Mentionnez les personnes qui devraient reviewer -->

@username pour review de la partie X
@username pour validation de Y

---

**Note pour les reviewers :** Merci de vérifier particulièrement [aspect spécifique] dans cette PR.
