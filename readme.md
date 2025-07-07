# 📊 Matrice de Corrélation Multi-Actifs

Une application web interactive pour visualiser et analyser les corrélations entre différents types d'actifs financiers : cryptomonnaies, actions, ETFs et matières premières.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Fonctionnalités

- **Multi-actifs** : Support des cryptomonnaies, actions, ETFs et matières premières
- **Périodes flexibles** : 30 jours, 90 jours, 6 mois, 1 an, ou depuis le début de l'année
- **Visualisations interactives** : 
  - Matrice de corrélation en heatmap
  - Corrélation glissante entre deux actifs
  - Statistiques détaillées par actif
- **Métriques avancées** :
  - Score de diversification du portefeuille
  - Identification des paires fortement corrélées
  - Calcul du Beta (vs S&P 500)
  - Ratio de Sharpe, volatilité, skewness, kurtosis
- **Export des données** : Téléchargement CSV de la matrice de corrélation
- **Interface moderne** : Design dark mode responsive

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Un navigateur web moderne

## 🛠️ Installation

### 1. Cloner le repository

```bash
git clone https://github.com/nohem-mg/Cross-Asset-Correlation-Matrix.git
cd correlation-matrix-app
```

### 2. Créer un environnement virtuel

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r backend/requirements.txt
```

### 4. Configuration

Créez un fichier `.env` à la racine du projet (voir `.env.example`) :

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
CORS_ORIGINS=http://localhost:8080
COINGECKO_API_KEY=  # Optionnel, pour des limites plus élevées
```

## 🚀 Démarrage

### 1. Lancer le serveur Flask

```bash
cd backend
python3 app.py
```

Le serveur démarrera sur `http://localhost:5000`

### 2. Ouvrir l'interface web

Ouvrez le fichier `frontend/index.html` dans votre navigateur, ou utilisez un serveur local :

```bash
# Avec Python
cd frontend
python3 -m http.server 8080

# Ou avec Node.js
npx serve frontend -p 8080
```

Accédez à l'application sur `http://localhost:8080`

## 📖 Guide d'utilisation

### 1. Sélection des actifs

1. Utilisez les onglets pour naviguer entre les catégories d'actifs
2. Cliquez sur les actifs pour les sélectionner (minimum 2)
3. Les actifs sélectionnés apparaissent en bas

### 2. Configuration de l'analyse

1. **Période** : Choisissez la période d'analyse
2. **Méthode** : Sélectionnez la méthode de corrélation (Pearson par défaut)

### 3. Analyse des résultats

- **Matrice de corrélation** : 
  - Vert = Corrélation positive forte
  - Rouge = Corrélation négative forte
  - Gris = Corrélation faible/nulle

- **Score de diversification** : 
  - > 0.7 = Excellente diversification
  - 0.4-0.7 = Diversification moyenne
  - < 0.4 = Faible diversification

### 4. Export des données

Cliquez sur "Exporter CSV" pour télécharger la matrice de corrélation

## 🏗️ Architecture

```
├── backend/
│   ├── app.py                 # Serveur Flask principal
│   ├── config.py             # Configuration
│   ├── data_fetcher.py       # Récupération des données
│   ├── correlation_calc.py   # Calculs statistiques
│   └── requirements.txt      # Dépendances Python
│
├── frontend/
│   ├── index.html           # Page principale
│   ├── css/
│   │   └── styles.css       # Styles
│   └── js/
│       ├── app.js          # Logique principale
│       ├── api.js          # Communication API
│       └── chart.js        # Visualisations
│
└── README.md
```

## 📊 Sources de données

- **Actions/ETFs/Matières premières** : Yahoo Finance (yfinance)
- **Cryptomonnaies** : CoinGecko API

## 🔧 Configuration avancée

### Ajouter de nouveaux actifs

Modifiez le fichier `backend/config.py` :

```python
CRYPTO_ASSETS = {
    'BTC': 'bitcoin',
    'NEW_COIN': 'new-coin-id',  # Ajouter ici
}
```

### Modifier les périodes disponibles

```python
TIME_PERIODS = {
    '7d': {'days': 7, 'label': '7 jours'},  # Nouvelle période
}
```

## 📈 Améliorations futures

- [ ] Support de plus de sources de données
- [ ] Backtesting de portefeuilles
- [ ] Optimisation de portefeuille (Markowitz)
- [ ] Alertes de corrélation
- [ ] Mode temps réel
- [ ] Export Excel avec graphiques
- [ ] API publique


## 🙏 Remerciements

- [Yahoo Finance](https://finance.yahoo.com/) pour les données de marché
- [CoinGecko](https://www.coingecko.com/) pour les données crypto
- [Plotly.js](https://plotly.com/javascript/) pour les visualisations
- [Flask](https://flask.palletsprojects.com/) pour le framework backend

---

Développé avec ❤️ pour la communauté financière