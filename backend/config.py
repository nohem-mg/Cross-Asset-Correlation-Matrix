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
        'AVAX': 'avalanche-2',
        'DOT': 'polkadot',
        'MATIC': 'matic-network',
        'LINK': 'chainlink'
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
        'SPY': 'SPDR S&P 500 ETF',
        'QQQ': 'Invesco QQQ Trust',
        'IWM': 'iShares Russell 2000 ETF',
        'EFA': 'iShares MSCI EAFE ETF',
        'GLD': 'SPDR Gold Shares',
        'VTI': 'Vanguard Total Stock Market ETF',
        'AGG': 'iShares Core U.S. Aggregate Bond ETF',
        'EEM': 'iShares MSCI Emerging Markets ETF'
    }
    
    COMMODITY_ASSETS = {
        'GC=F': 'Gold Futures',
        'SI=F': 'Silver Futures',
        'CL=F': 'Crude Oil Futures',
        'NG=F': 'Natural Gas Futures',
        'ZC=F': 'Corn Futures',
        'ZW=F': 'Wheat Futures'
    }
    
    # Time periods
    TIME_PERIODS = {
        '30d': {'days': 30, 'label': '30 jours'},
        '90d': {'days': 90, 'label': '90 jours'},
        '180d': {'days': 180, 'label': '6 mois'},
        '1y': {'days': 365, 'label': '1 an'},
        'ytd': {'label': 'Depuis début année'}
    }