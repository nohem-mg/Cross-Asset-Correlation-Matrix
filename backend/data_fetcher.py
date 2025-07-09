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
        crypto_ids = []
        for symbol in symbols:
            if symbol in Config.CRYPTO_ASSETS:
                # Use predefined mapping
                crypto_ids.append(Config.CRYPTO_ASSETS[symbol])
            else:
                # For custom assets, try to find the CoinGecko ID
                crypto_id = self._get_coingecko_id_for_symbol(symbol)
                crypto_ids.append(crypto_id if crypto_id else symbol.lower())
        
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
    
    def _get_coingecko_id_for_symbol(self, symbol: str) -> Optional[str]:
        """Get CoinGecko ID for a custom crypto symbol"""
        try:
            url = "https://api.coingecko.com/api/v3/search"
            params = {'query': symbol}
            
            if Config.COINGECKO_API_KEY:
                params['x_cg_pro_api_key'] = Config.COINGECKO_API_KEY
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            coins = data.get('coins', [])
            
            # Find exact symbol match
            for coin in coins:
                if coin['symbol'].upper() == symbol.upper():
                    return coin['id']
            
            return None
            
        except Exception as e:
            print(f"Error getting CoinGecko ID for {symbol}: {e}")
            return None
    
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

    def search_assets(self, query: str) -> List[Dict]:
        """Search for assets in both Yahoo Finance and CoinGecko"""
        results = []
        
        # Search in Yahoo Finance
        yahoo_results = self._search_yahoo_finance(query)
        results.extend(yahoo_results)
        
        # Search in CoinGecko
        coingecko_results = self._search_coingecko(query)
        results.extend(coingecko_results)
        
        # Remove duplicates and sort by relevance
        seen_symbols = set()
        unique_results = []
        for result in results:
            if result['symbol'] not in seen_symbols:
                seen_symbols.add(result['symbol'])
                unique_results.append(result)
        
        # Sort by relevance score (highest first), then by name
        unique_results.sort(key=lambda x: (-x.get('relevance', 0), x['name'].lower()))
        
        return unique_results[:20]  # Limit to 20 results
    
    def _search_yahoo_finance(self, query: str) -> List[Dict]:
        """Search for assets in Yahoo Finance using yfinance"""
        results = []
        
        try:
            # First, try to search in common stock/ETF/commodity mappings
            name_to_symbol_mappings = self._get_name_to_symbol_mappings()
            query_lower = query.lower()
            
            # Search by name in mappings with improved matching
            for name, symbol_info in name_to_symbol_mappings.items():
                name_lower = name.lower()
                # Check for exact word matches or partial matches
                if (query_lower in name_lower or 
                    any(word in name_lower for word in query_lower.split()) or
                    any(word in query_lower for word in name_lower.split())):
                    
                    # Try to get data for this symbol to validate it
                    try:
                        ticker = yf.Ticker(symbol_info['symbol'])
                        info = ticker.info
                        
                        if info and 'symbol' in info and info.get('regularMarketPrice'):
                            # Calculate relevance score for better ordering
                            relevance_score = 0
                            if query_lower == name_lower:
                                relevance_score = 100  # Exact match
                            elif name_lower.startswith(query_lower):
                                relevance_score = 90   # Starts with query
                            elif query_lower in name_lower:
                                relevance_score = 80   # Contains query
                            else:
                                relevance_score = 70   # Word match
                            
                            results.append({
                                'symbol': symbol_info['symbol'],
                                'name': name,
                                'source': 'yahoo',
                                'category': symbol_info['category'],
                                'price': info.get('regularMarketPrice'),
                                'currency': info.get('currency', 'USD'),
                                'relevance': relevance_score
                            })
                    except:
                        continue
            
            # Try searching with the query as a symbol (existing logic)
            symbols_to_try = [
                query.upper(),
                f"{query.upper()}.PA",  # Euronext Paris
                f"{query.upper()}.L",   # London Stock Exchange
                f"{query.upper()}.TO",  # Toronto Stock Exchange
                f"^{query.upper()}",    # Index
                f"{query.upper()}=F"    # Futures/Commodities
            ]
            
            for symbol in symbols_to_try:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    if info and 'symbol' in info and info.get('regularMarketPrice'):
                        name = info.get('longName', info.get('shortName', symbol))
                        if name and name != symbol:
                            # Check if we already have this symbol
                            if not any(r['symbol'] == symbol for r in results):
                                # Determine category based on asset type
                                category = self._determine_yahoo_category(info)
                                
                                # Calculate relevance for symbol-based search
                                symbol_relevance = 50  # Lower than name matches
                                if query.upper() == symbol:
                                    symbol_relevance = 95
                                elif symbol.startswith(query.upper()):
                                    symbol_relevance = 85
                                
                                results.append({
                                    'symbol': symbol,
                                    'name': name,
                                    'source': 'yahoo',
                                    'category': category,
                                    'price': info.get('regularMarketPrice'),
                                    'currency': info.get('currency', 'USD'),
                                    'relevance': symbol_relevance
                                })
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    continue  # Skip invalid symbols
                    
        except Exception as e:
            print(f"Error searching Yahoo Finance: {e}")
        
        return results
    
    def _get_name_to_symbol_mappings(self) -> Dict[str, Dict]:
        """Get a mapping of company/asset names to their symbols for search"""
        mappings = {}
        
        # Add from config
        for symbol, name in Config.STOCK_ASSETS.items():
            mappings[name] = {'symbol': symbol, 'category': 'stocks'}
        
        for symbol, name in Config.ETF_ASSETS.items():
            mappings[name] = {'symbol': symbol, 'category': 'etfs'}
            
        for symbol, name in Config.COMMODITY_ASSETS.items():
            mappings[name] = {'symbol': symbol, 'category': 'commodities'}
        
        # Add common additional mappings for popular searches
        additional_mappings = {
            # Tech companies
            'Apple': {'symbol': 'AAPL', 'category': 'stocks'},
            'Microsoft': {'symbol': 'MSFT', 'category': 'stocks'},
            'Google': {'symbol': 'GOOGL', 'category': 'stocks'},
            'Alphabet': {'symbol': 'GOOGL', 'category': 'stocks'},
            'Tesla': {'symbol': 'TSLA', 'category': 'stocks'},
            'Amazon': {'symbol': 'AMZN', 'category': 'stocks'},
            'Meta': {'symbol': 'META', 'category': 'stocks'},
            'Facebook': {'symbol': 'META', 'category': 'stocks'},
            'Netflix': {'symbol': 'NFLX', 'category': 'stocks'},
            'NVIDIA': {'symbol': 'NVDA', 'category': 'stocks'},
            'AMD': {'symbol': 'AMD', 'category': 'stocks'},
            'Intel': {'symbol': 'INTC', 'category': 'stocks'},
            
            # Other popular companies
            'Coca Cola': {'symbol': 'KO', 'category': 'stocks'},
            'Coca-Cola': {'symbol': 'KO', 'category': 'stocks'},
            'PepsiCo': {'symbol': 'PEP', 'category': 'stocks'},
            'Pepsi': {'symbol': 'PEP', 'category': 'stocks'},
            'Johnson & Johnson': {'symbol': 'JNJ', 'category': 'stocks'},
            'J&J': {'symbol': 'JNJ', 'category': 'stocks'},
            'Procter & Gamble': {'symbol': 'PG', 'category': 'stocks'},
            'P&G': {'symbol': 'PG', 'category': 'stocks'},
            'Walmart': {'symbol': 'WMT', 'category': 'stocks'},
            'Home Depot': {'symbol': 'HD', 'category': 'stocks'},
            'McDonalds': {'symbol': 'MCD', 'category': 'stocks'},
            'McDonald\'s': {'symbol': 'MCD', 'category': 'stocks'},
            'Disney': {'symbol': 'DIS', 'category': 'stocks'},
            'Walt Disney': {'symbol': 'DIS', 'category': 'stocks'},
            'Nike': {'symbol': 'NKE', 'category': 'stocks'},
            'Boeing': {'symbol': 'BA', 'category': 'stocks'},
            'Caterpillar': {'symbol': 'CAT', 'category': 'stocks'},
            'Exxon Mobil': {'symbol': 'XOM', 'category': 'stocks'},
            'Exxon': {'symbol': 'XOM', 'category': 'stocks'},
            'Chevron': {'symbol': 'CVX', 'category': 'stocks'},
            'Pfizer': {'symbol': 'PFE', 'category': 'stocks'},
            'Merck': {'symbol': 'MRK', 'category': 'stocks'},
            'IBM': {'symbol': 'IBM', 'category': 'stocks'},
            'Oracle': {'symbol': 'ORCL', 'category': 'stocks'},
            'Salesforce': {'symbol': 'CRM', 'category': 'stocks'},
            'Adobe': {'symbol': 'ADBE', 'category': 'stocks'},
            'PayPal': {'symbol': 'PYPL', 'category': 'stocks'},
            'Uber': {'symbol': 'UBER', 'category': 'stocks'},
            'Spotify': {'symbol': 'SPOT', 'category': 'stocks'},
            'Twitter': {'symbol': 'TWTR', 'category': 'stocks'},
            'Square': {'symbol': 'SQ', 'category': 'stocks'},
            'Block': {'symbol': 'SQ', 'category': 'stocks'},
            
            # German companies
            'SAP': {'symbol': 'SAP', 'category': 'stocks'},
            'Siemens': {'symbol': 'SIE.DE', 'category': 'stocks'},
            'Volkswagen': {'symbol': 'VOW3.DE', 'category': 'stocks'},
            'VW': {'symbol': 'VOW3.DE', 'category': 'stocks'},
            'BMW': {'symbol': 'BMW.DE', 'category': 'stocks'},
            'Mercedes': {'symbol': 'MBG.DE', 'category': 'stocks'},
            'Mercedes-Benz': {'symbol': 'MBG.DE', 'category': 'stocks'},
            'Daimler': {'symbol': 'MBG.DE', 'category': 'stocks'},
            'Bayer': {'symbol': 'BAYN.DE', 'category': 'stocks'},
            'BASF': {'symbol': 'BAS.DE', 'category': 'stocks'},
            'Adidas': {'symbol': 'ADS.DE', 'category': 'stocks'},
            'Allianz': {'symbol': 'ALV.DE', 'category': 'stocks'},
            
            # Financial
            'JPMorgan': {'symbol': 'JPM', 'category': 'stocks'},
            'JP Morgan': {'symbol': 'JPM', 'category': 'stocks'},
            'Visa': {'symbol': 'V', 'category': 'stocks'},
            'Mastercard': {'symbol': 'MA', 'category': 'stocks'},
            'Bank of America': {'symbol': 'BAC', 'category': 'stocks'},
            'Goldman Sachs': {'symbol': 'GS', 'category': 'stocks'},
            'Goldman': {'symbol': 'GS', 'category': 'stocks'},
            'Wells Fargo': {'symbol': 'WFC', 'category': 'stocks'},
            'Wells': {'symbol': 'WFC', 'category': 'stocks'},
            'Citigroup': {'symbol': 'C', 'category': 'stocks'},
            'Citi': {'symbol': 'C', 'category': 'stocks'},
            'Morgan Stanley': {'symbol': 'MS', 'category': 'stocks'},
            'American Express': {'symbol': 'AXP', 'category': 'stocks'},
            'Amex': {'symbol': 'AXP', 'category': 'stocks'},
            
            # French companies
            'LVMH': {'symbol': 'MC.PA', 'category': 'stocks'},
            'Total': {'symbol': 'TTE.PA', 'category': 'stocks'},
            'TotalEnergies': {'symbol': 'TTE.PA', 'category': 'stocks'},
            'Sanofi': {'symbol': 'SAN.PA', 'category': 'stocks'},
            'Airbus': {'symbol': 'AIR.PA', 'category': 'stocks'},
            'L\'Oréal': {'symbol': 'OR.PA', 'category': 'stocks'},
            'Loreal': {'symbol': 'OR.PA', 'category': 'stocks'},
            'Michelin': {'symbol': 'ML.PA', 'category': 'stocks'},
            'Compagnie Générale des Établissements Michelin': {'symbol': 'ML.PA', 'category': 'stocks'},
            'Schneider Electric': {'symbol': 'SU.PA', 'category': 'stocks'},
            'Schneider': {'symbol': 'SU.PA', 'category': 'stocks'},
            'Société Générale': {'symbol': 'GLE.PA', 'category': 'stocks'},
            'SocGen': {'symbol': 'GLE.PA', 'category': 'stocks'},
            'BNP Paribas': {'symbol': 'BNP.PA', 'category': 'stocks'},
            'BNP': {'symbol': 'BNP.PA', 'category': 'stocks'},
            'Dassault Systèmes': {'symbol': 'DSY.PA', 'category': 'stocks'},
            'Dassault': {'symbol': 'DSY.PA', 'category': 'stocks'},
            'Vinci': {'symbol': 'DG.PA', 'category': 'stocks'},
            'Saint-Gobain': {'symbol': 'SGO.PA', 'category': 'stocks'},
            'Saint Gobain': {'symbol': 'SGO.PA', 'category': 'stocks'},
            'Kering': {'symbol': 'KER.PA', 'category': 'stocks'},
            'Hermès': {'symbol': 'RMS.PA', 'category': 'stocks'},
            'Hermes': {'symbol': 'RMS.PA', 'category': 'stocks'},
            'Vivendi': {'symbol': 'VIV.PA', 'category': 'stocks'},
            'Orange': {'symbol': 'ORA.PA', 'category': 'stocks'},
            'Danone': {'symbol': 'BN.PA', 'category': 'stocks'},
            'Pernod Ricard': {'symbol': 'RI.PA', 'category': 'stocks'},
            'Pernod': {'symbol': 'RI.PA', 'category': 'stocks'},
            'Carrefour': {'symbol': 'CA.PA', 'category': 'stocks'},
            'Crédit Agricole': {'symbol': 'ACA.PA', 'category': 'stocks'},
            'Credit Agricole': {'symbol': 'ACA.PA', 'category': 'stocks'},
            'Renault': {'symbol': 'RNO.PA', 'category': 'stocks'},
            'Stellantis': {'symbol': 'STLA.PA', 'category': 'stocks'},
            'Peugeot': {'symbol': 'STLA.PA', 'category': 'stocks'},
            'Citroën': {'symbol': 'STLA.PA', 'category': 'stocks'},
            'Citroen': {'symbol': 'STLA.PA', 'category': 'stocks'},
            'Thales': {'symbol': 'HO.PA', 'category': 'stocks'},
            'Safran': {'symbol': 'SAF.PA', 'category': 'stocks'},
            'Veolia': {'symbol': 'VIE.PA', 'category': 'stocks'},
            'Suez': {'symbol': 'SEV.PA', 'category': 'stocks'},
            'ArcelorMittal': {'symbol': 'MT.PA', 'category': 'stocks'},
            'Arcelor Mittal': {'symbol': 'MT.PA', 'category': 'stocks'},
            'Essilor': {'symbol': 'EL.PA', 'category': 'stocks'},
            'EssilorLuxottica': {'symbol': 'EL.PA', 'category': 'stocks'},
            'Luxottica': {'symbol': 'EL.PA', 'category': 'stocks'},
            
            # ETFs
            'S&P 500': {'symbol': 'SPY', 'category': 'etfs'},
            'SP500': {'symbol': 'SPY', 'category': 'etfs'},
            'NASDAQ': {'symbol': 'QQQ', 'category': 'etfs'},
            'CAC 40': {'symbol': '^FCHI', 'category': 'etfs'},
            'CAC40': {'symbol': '^FCHI', 'category': 'etfs'},
            
            # Commodities
            'Gold': {'symbol': 'GC=F', 'category': 'commodities'},
            'Or': {'symbol': 'GC=F', 'category': 'commodities'},
            'Silver': {'symbol': 'SI=F', 'category': 'commodities'},
            'Argent': {'symbol': 'SI=F', 'category': 'commodities'},
            'Oil': {'symbol': 'CL=F', 'category': 'commodities'},
            'Crude Oil': {'symbol': 'CL=F', 'category': 'commodities'},
            'Pétrole': {'symbol': 'CL=F', 'category': 'commodities'},
            'Petrole': {'symbol': 'CL=F', 'category': 'commodities'},
        }
        
        mappings.update(additional_mappings)
        return mappings
    
    def _search_coingecko(self, query: str) -> List[Dict]:
        """Search for cryptocurrencies in CoinGecko"""
        results = []
        
        try:
            # First, try to search in crypto name mappings
            crypto_name_mappings = self._get_crypto_name_mappings()
            query_lower = query.lower()
            
            # Search by name in mappings with improved matching
            for name, crypto_info in crypto_name_mappings.items():
                name_lower = name.lower()
                # Check for exact word matches or partial matches
                if (query_lower in name_lower or 
                    any(word in name_lower for word in query_lower.split()) or
                    any(word in query_lower for word in name_lower.split())):
                    
                    # Try to get current price for validation
                    try:
                        price_url = f"https://api.coingecko.com/api/v3/simple/price"
                        price_params = {
                            'ids': crypto_info['id'],
                            'vs_currencies': 'usd'
                        }
                        
                        if Config.COINGECKO_API_KEY:
                            price_params['x_cg_pro_api_key'] = Config.COINGECKO_API_KEY
                        
                        price_response = requests.get(price_url, params=price_params)
                        if price_response.status_code == 200:
                            price_data = price_response.json()
                            current_price = price_data.get(crypto_info['id'], {}).get('usd')
                            
                            # Calculate relevance score
                            relevance_score = 0
                            if query_lower == name_lower:
                                relevance_score = 100  # Exact match
                            elif name_lower.startswith(query_lower):
                                relevance_score = 90   # Starts with query
                            elif query_lower in name_lower:
                                relevance_score = 80   # Contains query
                            else:
                                relevance_score = 70   # Word match
                            
                            results.append({
                                'symbol': crypto_info['symbol'].upper(),
                                'name': name,
                                'source': 'coingecko',
                                'category': 'crypto',
                                'coingecko_id': crypto_info['id'],
                                'price': current_price,
                                'relevance': relevance_score
                            })
                    except:
                        continue
            
            # Then use CoinGecko search API
            url = "https://api.coingecko.com/api/v3/search"
            params = {'query': query}
            
            if Config.COINGECKO_API_KEY:
                params['x_cg_pro_api_key'] = Config.COINGECKO_API_KEY
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Process coins
            for coin in data.get('coins', [])[:10]:  # Limit to 10 results
                # Check if we already have this coin
                if not any(r['symbol'] == coin['symbol'].upper() for r in results):
                    # Calculate relevance for API search results
                    api_relevance = 30  # Lower than direct mappings
                    if query.lower() == coin['name'].lower():
                        api_relevance = 60
                    elif coin['name'].lower().startswith(query.lower()):
                        api_relevance = 55
                    elif query.lower() == coin['symbol'].lower():
                        api_relevance = 50
                    elif coin['symbol'].lower().startswith(query.lower()):
                        api_relevance = 45
                    
                    results.append({
                        'symbol': coin['symbol'].upper(),
                        'name': coin['name'],
                        'source': 'coingecko',
                        'category': 'crypto',
                        'coingecko_id': coin['id'],
                        'market_cap_rank': coin.get('market_cap_rank'),
                        'relevance': api_relevance
                    })
            
        except Exception as e:
            print(f"Error searching CoinGecko: {e}")
        
        return results
    
    def _get_crypto_name_mappings(self) -> Dict[str, Dict]:
        """Get a mapping of crypto names to their CoinGecko info for search"""
        mappings = {}
        
        # Add from config
        for symbol, coingecko_id in Config.CRYPTO_ASSETS.items():
            # Get display name from config
            display_name = Config.DISPLAY_NAMES.get(symbol, symbol)
            mappings[display_name] = {'symbol': symbol, 'id': coingecko_id}
        
        # Add common additional crypto mappings
        additional_mappings = {
            # Popular cryptocurrencies
            'Bitcoin': {'symbol': 'BTC', 'id': 'bitcoin'},
            'Ethereum': {'symbol': 'ETH', 'id': 'ethereum'},
            'Solana': {'symbol': 'SOL', 'id': 'solana'},
            'Binance Coin': {'symbol': 'BNB', 'id': 'binancecoin'},
            'BNB': {'symbol': 'BNB', 'id': 'binancecoin'},
            'Ripple': {'symbol': 'XRP', 'id': 'ripple'},
            'XRP': {'symbol': 'XRP', 'id': 'ripple'},
            'Cardano': {'symbol': 'ADA', 'id': 'cardano'},
            'Polygon': {'symbol': 'MATIC', 'id': 'matic-network'},
            'Matic': {'symbol': 'MATIC', 'id': 'matic-network'},
            'Chainlink': {'symbol': 'LINK', 'id': 'chainlink'},
            'Polkadot': {'symbol': 'DOT', 'id': 'polkadot'},
            'Avalanche': {'symbol': 'AVAX', 'id': 'avalanche-2'},
            'Dogecoin': {'symbol': 'DOGE', 'id': 'dogecoin'},
            'Shiba Inu': {'symbol': 'SHIB', 'id': 'shiba-inu'},
            'Litecoin': {'symbol': 'LTC', 'id': 'litecoin'},
            'Bitcoin Cash': {'symbol': 'BCH', 'id': 'bitcoin-cash'},
            'Uniswap': {'symbol': 'UNI', 'id': 'uniswap'},
            'Cosmos': {'symbol': 'ATOM', 'id': 'cosmos'},
            'Filecoin': {'symbol': 'FIL', 'id': 'filecoin'},
            'TRON': {'symbol': 'TRX', 'id': 'tron'},
            'Stellar': {'symbol': 'XLM', 'id': 'stellar'},
            'VeChain': {'symbol': 'VET', 'id': 'vechain'},
            'Internet Computer': {'symbol': 'ICP', 'id': 'internet-computer'},
            'Algorand': {'symbol': 'ALGO', 'id': 'algorand'},
            'Tezos': {'symbol': 'XTZ', 'id': 'tezos'},
            'Monero': {'symbol': 'XMR', 'id': 'monero'},
            'EOS': {'symbol': 'EOS', 'id': 'eos'},
            'Aave': {'symbol': 'AAVE', 'id': 'aave'},
            'Maker': {'symbol': 'MKR', 'id': 'maker'},
            'Compound': {'symbol': 'COMP', 'id': 'compound-governance-token'},
        }
        
        mappings.update(additional_mappings)
        return mappings
    
    def _determine_yahoo_category(self, info: Dict) -> str:
        """Determine asset category from Yahoo Finance info"""
        quote_type = info.get('quoteType', '').lower()
        symbol = info.get('symbol', '')
        
        if quote_type == 'cryptocurrency':
            return 'crypto'
        elif quote_type == 'etf':
            return 'etfs'
        elif quote_type == 'future' or '=F' in symbol:
            return 'commodities'
        elif quote_type in ['equity', 'stock']:
            return 'stocks'
        elif symbol.startswith('^'):
            return 'etfs'  # Indices are treated as ETFs
        else:
            return 'stocks'  # Default fallback
    
    def validate_asset(self, symbol: str, source: str) -> Dict:
        """Validate that an asset exists and can be fetched"""
        try:
            if source == 'yahoo':
                return self._validate_yahoo_asset(symbol)
            elif source == 'coingecko':
                return self._validate_coingecko_asset(symbol)
            else:
                return {'valid': False, 'error': 'Invalid source'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _validate_yahoo_asset(self, symbol: str) -> Dict:
        """Validate a Yahoo Finance asset"""
        try:
            ticker = yf.Ticker(symbol)
            # Try to get recent data
            hist = ticker.history(period="5d")
            
            if hist.empty:
                return {'valid': False, 'error': f'No data available for symbol {symbol}'}
            
            info = ticker.info
            name = info.get('longName', info.get('shortName', symbol))
            
            return {
                'valid': True,
                'name': name,
                'current_price': info.get('regularMarketPrice'),
                'currency': info.get('currency', 'USD')
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'Cannot fetch data for {symbol}: {str(e)}'}
    
    def _validate_coingecko_asset(self, symbol: str) -> Dict:
        """Validate a CoinGecko asset"""
        try:
            # First, search for the coin to get its ID
            url = "https://api.coingecko.com/api/v3/search"
            params = {'query': symbol}
            
            if Config.COINGECKO_API_KEY:
                params['x_cg_pro_api_key'] = Config.COINGECKO_API_KEY
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            coins = data.get('coins', [])
            
            # Find exact symbol match
            coin_id = None
            coin_name = None
            for coin in coins:
                if coin['symbol'].upper() == symbol.upper():
                    coin_id = coin['id']
                    coin_name = coin['name']
                    break
            
            if not coin_id:
                return {'valid': False, 'error': f'Cryptocurrency {symbol} not found'}
            
            # Try to get price data
            price_url = f"https://api.coingecko.com/api/v3/simple/price"
            price_params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }
            
            if Config.COINGECKO_API_KEY:
                price_params['x_cg_pro_api_key'] = Config.COINGECKO_API_KEY
            
            price_response = requests.get(price_url, params=price_params)
            price_response.raise_for_status()
            
            price_data = price_response.json()
            current_price = price_data.get(coin_id, {}).get('usd')
            
            return {
                'valid': True,
                'name': coin_name,
                'coingecko_id': coin_id,
                'current_price': current_price,
                'currency': 'USD'
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'Cannot validate {symbol}: {str(e)}'}