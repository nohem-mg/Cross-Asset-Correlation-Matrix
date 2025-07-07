import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # API configuration
    COINGECKO_API_KEY = os.environ.get('COINGECKO_API_KEY', '')
    
    # Cache settings
    CACHE_DURATION = int(os.environ.get('CACHE_DURATION', 300))  # 5 minutes
    
    # Available assets
    CRYPTO_ASSETS = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'SOL': 'solana',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'ADA': 'cardano',
        'AVAX':'avalanche-2',
        'DOT': 'polkadot',
        'MATIC': 'matic-network',
        'LINK': 'chainlink',
        'HYPE': 'hyperliquid'
    }
    
    STOCK_ASSETS = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'GOOGL': 'Alphabet Inc.',
        'TSLA': 'Tesla, Inc.',
        'AMZN': 'Amazon.com, Inc.',
        'META': 'Meta Platforms, Inc.',
        'NVDA': 'NVIDIA Corporation',
        'JPM': 'JPMorgan Chase & Co.',
        'V': 'Visa Inc.',
        'JNJ': 'Johnson & Johnson'
    }
    
    ETF_ASSETS = {
        'SPY': 'S&P 500 Index',
        'QQQ': 'Invesco QQQ Trust',
        'IWM': 'iShares Russell 2000 ETF',
        'EFA': 'iShares MSCI EAFE ETF',
        'VTI': 'Vanguard Total Stock Market ETF',
        'AGG': 'iShares Core U.S. Aggregate Bond ETF',
        'EEM': 'iShares MSCI Emerging Markets ETF',
        '^FCHI': 'CAC 40 Index',
        'WPEA.PA': 'iShares MSCI World ETF',

    }
    
    COMMODITY_ASSETS = {
        'GC=F': 'Gold',
        'SI=F': 'Silver',
        'CL=F': 'Oil',
        'NG=F': 'Natural Gas',
        'ZC=F': 'Corn',
        'ZW=F': 'Wheat'
    }
    
    # Mapping des symboles d'affichage (symbole technique -> symbole affiché)
    DISPLAY_SYMBOLS = {
        # Crypto - garder les symboles standards
        'BTC': 'BTC',
        'ETH': 'ETH',
        'SOL': 'SOL',
        'BNB': 'BNB',
        'XRP': 'XRP',
        'ADA': 'ADA',
        'AVAX': 'AVAX',
        'DOT': 'DOT',
        'MATIC': 'MATIC',
        'LINK': 'LINK',
        'HYPE': 'HYPE',
        
        # Actions - garder les symboles standards
        'AAPL': 'AAPL',
        'MSFT': 'MSFT',
        'GOOGL': 'GOOGL',
        'TSLA': 'TSLA',
        'AMZN': 'AMZN',
        'META': 'META',
        'NVDA': 'NVDA',
        'JPM': 'JPM',
        'V': 'V',
        'JNJ': 'JNJ',
        
        # ETFs - symboles personnalisés
        'SPY': 'SP500',
        'QQQ': 'QQQ',
        'IWM': 'IWM',
        'EFA': 'EFA',
        'GLD': 'GLD',
        'VTI': 'VTI',
        'AGG': 'AGG',
        'EEM': 'EEM',
        '^FCHI': 'CAC40',
        'WPEA.PA': 'WPEA',
        
        # Matières premières - symboles personnalisés
        'GC=F': 'GOLD',
        'SI=F': 'SILVER',
        'CL=F': 'OIL',
        'NG=F': 'NATGAS',
        'ZC=F': 'CORN',
        'ZW=F': 'WHEAT'
    }
    
    # Mapping des noms d'affichage (symbole technique -> nom affiché)
    DISPLAY_NAMES = {
        # Crypto - noms propres
        'BTC': 'Bitcoin',
        'ETH': 'Ethereum',
        'SOL': 'Solana',
        'BNB': 'Binance Coin',
        'XRP': 'Ripple',
        'ADA': 'Cardano',
        'AVAX': 'Avalanche',
        'DOT': 'Polkadot',
        'MATIC': 'Polygon',
        'LINK': 'Chainlink',
        'HYPE': 'Hyperliquid',
        
        # Actions - noms courts
        'AAPL': 'Apple',
        'MSFT': 'Microsoft',
        'GOOGL': 'Google',
        'TSLA': 'Tesla',
        'AMZN': 'Amazon',
        'META': 'Meta',
        'NVDA': 'NVIDIA',
        'JPM': 'JPMorgan',
        'V': 'Visa',
        'JNJ': 'Johnson & Johnson',
        
        # ETFs - noms courts
        'SPY': 'S&P 500',
        'QQQ': 'NASDAQ 100',
        'IWM': 'Russell 2000',
        'EFA': 'MSCI EAFE',
        'VTI': 'Total Stock Market',
        'AGG': 'US Bonds',
        'EEM': 'MSCI Emerging Markets',
        '^FCHI': 'CAC 40',
        'WPEA.PA': 'MSCI World',
        
        # Matières premières - noms français
        'GC=F': 'Or',
        'SI=F': 'Argent',
        'CL=F': 'Pétrole',
        'NG=F': 'Gaz Naturel',
        'ZC=F': 'Maïs',
        'ZW=F': 'Blé'
    }
    
    # Time periods
    TIME_PERIODS = {
        '7d': {'days': 7, 'label': '7 jours'},
        '30d': {'days': 30, 'label': '30 jours'},
        '90d': {'days': 90, 'label': '90 jours'},
        '180d': {'days': 180, 'label': '6 mois'},
        '1y': {'days': 365, 'label': '1 an'},
        'ytd': {'label': 'Depuis début année'}
    }