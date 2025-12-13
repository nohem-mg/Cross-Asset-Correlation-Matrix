# Guide de Déploiement

Cette application nécessite le déploiement de deux composants :
1. **Frontend** (HTML/CSS/JS) - peut être déployé sur Vercel, Netlify, GitHub Pages
2. **Backend** (Flask/Python) - doit être déployé sur Render, Railway, ou Heroku

## Option 1 : Déploiement sur Render (Recommandé)

### Backend (Render)

1. Créez un compte sur [render.com](https://render.com)
2. Créez un nouveau "Web Service"
3. Connectez votre repository GitHub
4. Configurez :
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3
5. Notez l'URL générée (ex: `https://votre-app.onrender.com`)

### Frontend (Render ou Vercel)

1. Modifiez `frontend/js/config.js` :
```javascript
window.API_BASE_URL = 'https://votre-backend.onrender.com/api';
```

2. Déployez le frontend sur Vercel/Netlify ou Render Static Site

## Option 2 : Déploiement sur Railway

### Backend

1. Créez un compte sur [railway.app](https://railway.app)
2. Nouveau projet > Deploy from GitHub
3. Sélectionnez le dossier `backend`
4. Railway détectera automatiquement Flask
5. Notez l'URL générée

### Frontend

Même procédure que l'Option 1.

## Option 3 : Tout sur Heroku

```bash
# Depuis la racine du projet
heroku create votre-app-name
git push heroku main
```

Nécessite un `Procfile` à la racine :
```
web: cd backend && gunicorn app:app
```

## Configuration du Frontend pour la Production

Modifiez `frontend/js/config.js` :

```javascript
(function() {
    // Remplacez par l'URL de votre backend déployé
    window.API_BASE_URL = 'https://votre-backend-url.com/api';
})();
```

## Variables d'Environnement Backend

Configurez ces variables sur votre plateforme de déploiement :

| Variable | Description | Exemple |
|----------|-------------|---------|
| `CORS_ORIGINS` | Domaines autorisés | `https://votre-frontend.vercel.app` |
| `COINGECKO_API_KEY` | (Optionnel) Clé API CoinGecko | `CG-xxx...` |
| `DEBUG` | Mode debug | `False` |

## Fichier requirements.txt pour Render

Ajoutez `gunicorn` au fichier `backend/requirements.txt` pour la production :

```
Flask>=3.0.0
Flask-CORS>=4.0.0
yfinance>=0.2.40
pandas>=2.1.4
numpy>=1.26.2
requests>=2.31.0
python-dotenv>=1.0.0
scipy>=1.11.4
gunicorn>=21.0.0
```

## Test Local

```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
python app.py

# Terminal 2 - Frontend
cd frontend
python -m http.server 8080
# Ouvrir http://localhost:8080
```
