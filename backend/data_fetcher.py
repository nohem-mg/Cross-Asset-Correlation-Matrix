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
                
                # Remove timezone info to match stock data
                df.index = df.index.tz_localize(None)
                
                # Normalize to daily data (end of day)
                df = df.resample('D').last()
                
                data_dict[symbol] = df[symbol]
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error fetching crypto data for {symbol}: {e}")
                continue
        
        if data_dict:
            result = pd.DataFrame(data_dict)
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
            # Handle single vs multiple symbols differently
            if len(symbols) == 1:
                # For single symbol, use Ticker object
                ticker = yf.Ticker(symbols[0])
                hist = ticker.history(start=start_date, end=end_date, auto_adjust=True)
                if hist.empty:
                    print(f"No data returned for {symbols[0]}")
                    return pd.DataFrame()
                result = pd.DataFrame({symbols[0]: hist['Close']})
            else:
                # For multiple symbols, use download
                data = yf.download(
                    symbols,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    auto_adjust=True,
                    group_by='ticker'
                )
                
                if data.empty:
                    print("No data returned from Yahoo Finance")
                    return pd.DataFrame()
                
                # Extract Close prices
                if len(symbols) > 1:
                    if 'Close' in data.columns.get_level_values(1):
                        # Multi-level columns (ticker, metric)
                        result = data.xs('Close', axis=1, level=1)
                    else:
                        # Single level columns
                        result = data['Close']
                else:
                    result = pd.DataFrame({symbols[0]: data['Close']})
            
            # Ensure index is datetime without timezone
            result.index = pd.to_datetime(result.index)
            if result.index.tz is not None:
                result.index = result.index.tz_localize(None)
            
            self.cache[cache_key] = result
            self.cache_timestamps[cache_key] = time.time()
            
            return result
            
        except Exception as e:
            print(f"Error fetching stock data: {e}")
            print(f"Symbols: {symbols}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def fetch_mixed_assets(self, assets: Dict[str, List[str]], period: str) -> pd.DataFrame:
        """Fetch data for mixed asset types with better alignment"""
        all_data = []
        
        # Debug print
        print(f"Fetching mixed assets: {assets}")
        
        # Fetch crypto data
        if 'crypto' in assets and assets['crypto']:
            crypto_data = self.fetch_crypto_data(assets['crypto'], period)
            if not crypto_data.empty:
                print(f"Crypto data shape: {crypto_data.shape}")
                all_data.append(crypto_data)
        
        # Fetch stock data (including ETFs and commodities)
        stock_symbols = []
        for asset_type in ['stocks', 'etfs', 'commodities']:
            if asset_type in assets and assets[asset_type]:
                stock_symbols.extend(assets[asset_type])
        
        if stock_symbols:
            stock_data = self.fetch_stock_data(stock_symbols, period)
            if not stock_data.empty:
                print(f"Stock data shape: {stock_data.shape}")
                all_data.append(stock_data)
        
        # Combine all data with better alignment
        if all_data:
            # Use outer join to keep all data
            combined = pd.concat(all_data, axis=1, join='outer')
            
            # Sort by index to ensure chronological order
            combined = combined.sort_index()
            
            # Forward fill first (to handle weekends/holidays)
            combined = combined.ffill()
            
            # Then backward fill for any remaining NaN at the beginning
            combined = combined.bfill()
            
            # Drop any rows where all values are still NaN
            combined = combined.dropna(how='all')
            
            # Drop any rows with any NaN (to ensure correlation calculation works)
            combined = combined.dropna()
            
            # Debug print
            print(f"Combined data shape after cleaning: {combined.shape}")
            print(f"Columns in combined data: {combined.columns.tolist()}")
            
            # Ensure we have enough data points
            if len(combined) < 10:
                print(f"Warning: Only {len(combined)} data points after alignment")
            
            return combined
        
        return pd.DataFrame()
    
    def get_latest_prices(self, assets: Dict[str, List[str]]) -> Dict[str, float]:
        """Get latest prices for all assets"""
        prices = {}
        
        # Get 7 days of data to ensure we have recent prices
        data = self.fetch_mixed_assets(assets, '30d')
        
        if not data.empty:
            # Get the last valid price for each asset
            for symbol in data.columns:
                last_valid_idx = data[symbol].last_valid_index()
                if last_valid_idx is not None:
                    prices[symbol] = float(data.loc[last_valid_idx, symbol])
        
        return prices