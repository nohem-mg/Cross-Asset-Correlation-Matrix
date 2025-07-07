import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
from config import Config

class DataFetcher:
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache_timestamps:
            return False
        return (time.time() - self.cache_timestamps[key]) < Config.CACHE_DURATION
    
    def fetch_crypto_data(self, symbols: List[str], period: str) -> pd.DataFrame:
        """Fetch cryptocurrency data from CoinGecko API"""
        cache_key = f"crypto_{'-'.join(symbols)}_{period}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # Convert symbols to CoinGecko IDs
        crypto_ids = [Config.CRYPTO_ASSETS.get(symbol, symbol.lower()) for symbol in symbols]
        
        # Calculate date range
        end_date = datetime.now()
        if period == 'ytd':
            start_date = datetime(end_date.year, 1, 1)
            days = (end_date - start_date).days
        else:
            days = Config.TIME_PERIODS[period]['days']
            start_date = end_date - timedelta(days=days)
        
        # Prepare data
        data_dict = {}
        
        for symbol, crypto_id in zip(symbols, crypto_ids):
            try:
                # CoinGecko API endpoint
                url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'daily'
                }
                
                if Config.COINGECKO_API_KEY:
                    params['x_cg_pro_api_key'] = Config.COINGECKO_API_KEY
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                prices = data['prices']
                
                # Convert to DataFrame
                df = pd.DataFrame(prices, columns=['timestamp', symbol])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                data_dict[symbol] = df[symbol]
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error fetching crypto data for {symbol}: {e}")
                continue
        
        if data_dict:
            result = pd.DataFrame(data_dict)
            result = result.fillna(method='ffill').fillna(method='bfill')
            self.cache[cache_key] = result
            self.cache_timestamps[cache_key] = time.time()
            return result
        
        return pd.DataFrame()
    
    def fetch_stock_data(self, symbols: List[str], period: str) -> pd.DataFrame:
        """Fetch stock/ETF/commodity data from Yahoo Finance"""
        cache_key = f"stock_{'-'.join(symbols)}_{period}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # Calculate date range
        end_date = datetime.now()
        if period == 'ytd':
            start_date = datetime(end_date.year, 1, 1)
        else:
            days = Config.TIME_PERIODS[period]['days']
            start_date = end_date - timedelta(days=days)
        
        try:
            # Download data from Yahoo Finance
            data = yf.download(
                symbols,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True
            )
            
            # Handle single symbol case
            if len(symbols) == 1:
                result = pd.DataFrame({symbols[0]: data['Close']})
            else:
                result = data['Close']
            
            # Clean data
            result = result.fillna(method='ffill').fillna(method='bfill')
            
            self.cache[cache_key] = result
            self.cache_timestamps[cache_key] = time.time()
            
            return result
            
        except Exception as e:
            print(f"Error fetching stock data: {e}")
            return pd.DataFrame()
    
    def fetch_mixed_assets(self, assets: Dict[str, List[str]], period: str) -> pd.DataFrame:
        """Fetch data for mixed asset types"""
        all_data = []
        
        # Fetch crypto data
        if 'crypto' in assets and assets['crypto']:
            crypto_data = self.fetch_crypto_data(assets['crypto'], period)
            if not crypto_data.empty:
                all_data.append(crypto_data)
        
        # Fetch stock data
        stock_symbols = []
        for asset_type in ['stocks', 'etfs', 'commodities']:
            if asset_type in assets:
                stock_symbols.extend(assets[asset_type])
        
        if stock_symbols:
            stock_data = self.fetch_stock_data(stock_symbols, period)
            if not stock_data.empty:
                all_data.append(stock_data)
        
        # Combine all data
        if all_data:
            combined = pd.concat(all_data, axis=1, join='outer')
            # Align dates
            combined = combined.fillna(method='ffill').fillna(method='bfill')
            return combined
        
        return pd.DataFrame()
    
    def get_latest_prices(self, assets: Dict[str, List[str]]) -> Dict[str, float]:
        """Get latest prices for all assets"""
        prices = {}
        
        # Get 7 days of data to ensure we have recent prices
        data = self.fetch_mixed_assets(assets, '30d')
        
        if not data.empty:
            latest_prices = data.iloc[-1]
            for symbol, price in latest_prices.items():
                if not pd.isna(price):
                    prices[symbol] = float(price)
        
        return prices