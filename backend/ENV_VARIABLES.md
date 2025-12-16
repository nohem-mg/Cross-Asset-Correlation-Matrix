# Variables d'Environnement du Backend

Ce document liste toutes les variables d'environnement utilisées par le backend.

## Variables Requises

### `SECRET_KEY`
- **Description**: Clé secrète Flask pour la sécurité des sessions
- **Valeur par défaut**: `'dev-secret-key'`
- **Production**: Générer une clé aléatoire sécurisée
- **Exemple**: `SECRET_KEY=your-super-secret-key-here`

### `DEBUG`
- **Description**: Active le mode debug de Flask
- **Valeur par défaut**: `'True'`
- **Production**: Doit être `'False'`
- **Exemple**: `DEBUG=False`

## Variables Optionnelles mais Recommandées

### `CORS_ORIGINS`
- **Description**: Origines autorisées pour CORS (séparées par des virgules)
- **Valeur par défaut**: `'*'` (toutes les origines)
- **Production**: Spécifier les domaines exacts de votre frontend
- **Exemple**: `CORS_ORIGINS=https://votre-app.vercel.app,https://www.votre-domaine.com`

### `COINGECKO_API_KEY`
- **Description**: Clé API CoinGecko pour éviter les limites de taux
- **Valeur par défaut**: `''` (vide)
- **Recommandé**: Obtenir une clé sur https://www.coingecko.com/en/api
- **Exemple**: `COINGECKO_API_KEY=CG-xxxxxxxxxxxxx`

### `CACHE_DURATION`
- **Description**: Durée du cache en secondes
- **Valeur par défaut**: `300` (5 minutes)
- **Exemple**: `CACHE_DURATION=600` (10 minutes)

## Configuration pour le Déploiement

### Sur Render.com

1. Allez dans votre service web sur Render
2. Cliquez sur "Environment" dans le menu de gauche
3. Ajoutez les variables suivantes :

```
SECRET_KEY=<générez une clé aléatoire>
DEBUG=False
CORS_ORIGINS=https://votre-frontend.vercel.app
COINGECKO_API_KEY=<votre clé si vous en avez une>
CACHE_DURATION=300
```

### Sur Railway.app

1. Allez dans votre projet sur Railway
2. Cliquez sur votre service
3. Allez dans l'onglet "Variables"
4. Ajoutez les mêmes variables que ci-dessus

### Sur Heroku

```bash
heroku config:set SECRET_KEY="votre-clé-secrète"
heroku config:set DEBUG="False"
heroku config:set CORS_ORIGINS="https://votre-frontend.vercel.app"
heroku config:set COINGECKO_API_KEY="votre-clé-coingecko"
```

## Générer une SECRET_KEY sécurisée

En Python :
```python
import secrets
print(secrets.token_hex(32))
```

Ou en ligne de commande :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

