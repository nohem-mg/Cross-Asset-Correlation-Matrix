import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats as scipy_stats  # Renommé pour éviter le conflit
import logging

logger = logging.getLogger(__name__)

class CorrelationCalculator:

    @staticmethod
    def calculate_returns(prices_df: pd.DataFrame, method: str = 'log') -> pd.DataFrame:
        """Calculate returns from price data with validation"""
        if prices_df.empty:
            logger.warning("Empty price dataframe provided")
            return pd.DataFrame()

        # Check for zero or negative prices which would break log returns
        if method == 'log':
            if (prices_df <= 0).any().any():
                logger.warning("Found zero or negative prices, using simple returns instead")
                method = 'simple'

        if method == 'log':
            # Log returns - more suitable for financial analysis
            returns = np.log(prices_df / prices_df.shift(1))
        else:
            # Simple returns
            returns = prices_df.pct_change()

        # Remove first row (NaN) and any remaining NaN/inf values
        returns = returns.dropna()
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()

        if returns.empty:
            logger.warning("No valid returns calculated")

        return returns
    
    @staticmethod
    def calculate_correlation_matrix(returns_df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
        """Calculate correlation matrix with validation"""
        if returns_df.empty:
            logger.warning("Empty returns dataframe provided")
            return pd.DataFrame()

        if len(returns_df) < 5:
            logger.warning(f"Only {len(returns_df)} data points - correlation may be unreliable")

        valid_methods = ['pearson', 'spearman', 'kendall']
        if method not in valid_methods:
            logger.warning(f"Unknown method {method}, using pearson")
            method = 'pearson'

        try:
            corr_matrix = returns_df.corr(method=method)

            # Validate the correlation matrix
            if corr_matrix.isnull().any().any():
                logger.warning("Correlation matrix contains NaN values")
                # Fill NaN with 0 (no correlation) for assets with insufficient data
                corr_matrix = corr_matrix.fillna(0)

            return corr_matrix

        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()
    

    
    @staticmethod
    def calculate_diversification_score(corr_matrix: pd.DataFrame) -> float:
        """
        Calculate portfolio diversification score
        Score ranges from 0 (perfectly correlated) to 1 (perfectly uncorrelated)
        """
        n = len(corr_matrix)
        if n <= 1:
            return 0.0
        
        # Get upper triangle of correlation matrix (excluding diagonal)
        upper_triangle = np.triu(corr_matrix.values, k=1)
        correlations = upper_triangle[upper_triangle != 0]
        
        # Average absolute correlation
        avg_abs_corr = np.mean(np.abs(correlations))
        
        # Diversification score (1 - average absolute correlation)
        diversification_score = 1 - avg_abs_corr
        
        return float(diversification_score)
    
    @staticmethod
    def find_correlated_pairs(corr_matrix: pd.DataFrame, 
                            threshold: float = 0.7,
                            correlation_type: str = 'positive') -> List[Dict]:
        """Find highly correlated asset pairs"""
        pairs = []
        
        # Get upper triangle indices
        n = len(corr_matrix)
        for i in range(n):
            for j in range(i + 1, n):
                corr_value = corr_matrix.iloc[i, j]
                
                if correlation_type == 'positive' and corr_value >= threshold:
                    pairs.append({
                        'asset1': corr_matrix.index[i],
                        'asset2': corr_matrix.columns[j],
                        'correlation': float(corr_value)
                    })
                elif correlation_type == 'negative' and corr_value <= -threshold:
                    pairs.append({
                        'asset1': corr_matrix.index[i],
                        'asset2': corr_matrix.columns[j],
                        'correlation': float(corr_value)
                    })
                elif correlation_type == 'both' and abs(corr_value) >= threshold:
                    pairs.append({
                        'asset1': corr_matrix.index[i],
                        'asset2': corr_matrix.columns[j],
                        'correlation': float(corr_value)
                    })
        
        # Sort by absolute correlation value
        pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return pairs
    
    @staticmethod
    def calculate_statistics(returns_df: pd.DataFrame) -> Dict:
        """Calculate various statistics for each asset with error handling"""
        statistics = {}

        if returns_df.empty:
            logger.warning("Empty returns dataframe for statistics calculation")
            return statistics

        for asset in returns_df.columns:
            asset_returns = returns_df[asset].dropna()

            if len(asset_returns) < 2:
                logger.warning(f"Insufficient data for {asset} statistics")
                statistics[asset] = {
                    'mean_return': 0.0,
                    'volatility': 0.0,
                    'sharpe_ratio': 0.0,
                    'skewness': 0.0,
                    'kurtosis': 0.0,
                    'max_return': 0.0,
                    'min_return': 0.0,
                    'positive_days': 0,
                    'negative_days': 0,
                    'total_days': len(asset_returns)
                }
                continue

            try:
                mean_return = float(asset_returns.mean())
                volatility = float(asset_returns.std())

                # Annualized Sharpe ratio (assuming daily returns)
                sharpe_ratio = 0.0
                if volatility > 0:
                    sharpe_ratio = float(mean_return / volatility * np.sqrt(252))

                # Handle potential issues with skewness and kurtosis
                try:
                    skewness = float(scipy_stats.skew(asset_returns))
                    kurtosis = float(scipy_stats.kurtosis(asset_returns))
                except Exception:
                    skewness = 0.0
                    kurtosis = 0.0

                statistics[asset] = {
                    'mean_return': mean_return,
                    'volatility': volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'skewness': skewness,
                    'kurtosis': kurtosis,
                    'max_return': float(asset_returns.max()),
                    'min_return': float(asset_returns.min()),
                    'positive_days': int((asset_returns > 0).sum()),
                    'negative_days': int((asset_returns < 0).sum()),
                    'total_days': len(asset_returns)
                }

            except Exception as e:
                logger.error(f"Error calculating statistics for {asset}: {e}")
                statistics[asset] = {
                    'mean_return': 0.0,
                    'volatility': 0.0,
                    'sharpe_ratio': 0.0,
                    'skewness': 0.0,
                    'kurtosis': 0.0,
                    'max_return': 0.0,
                    'min_return': 0.0,
                    'positive_days': 0,
                    'negative_days': 0,
                    'total_days': 0
                }

        return statistics
    
    @staticmethod
    def calculate_beta(returns_df: pd.DataFrame, market_asset: str = 'SPY') -> Dict[str, float]:
        """Calculate beta for each asset relative to market (default SPY)"""
        betas = {}
        
        if market_asset not in returns_df.columns:
            return betas
        
        market_returns = returns_df[market_asset].dropna()
        market_variance = market_returns.var()
        
        for asset in returns_df.columns:
            if asset == market_asset:
                betas[asset] = 1.0
                continue
            
            asset_returns = returns_df[asset].dropna()
            
            # Align returns
            aligned_returns = pd.concat([asset_returns, market_returns], axis=1, join='inner')
            
            if len(aligned_returns) > 1:
                covariance = aligned_returns.cov().iloc[0, 1]
                beta = covariance / market_variance if market_variance > 0 else 0
                betas[asset] = float(beta)
            else:
                betas[asset] = 0.0
        
        return betas
    
    @staticmethod
    def calculate_performance_comparison(prices_df: pd.DataFrame) -> Dict:
        """Calculate performance comparison for all assets over the period"""
        if prices_df.empty:
            return {}
        
        # Calculate total return for each asset
        first_prices = prices_df.iloc[0]
        last_prices = prices_df.iloc[-1]
        
        performance_data = {}
        
        for asset in prices_df.columns:
            if pd.notna(first_prices[asset]) and pd.notna(last_prices[asset]) and first_prices[asset] > 0:
                total_return = ((last_prices[asset] - first_prices[asset]) / first_prices[asset]) * 100
                performance_data[asset] = {
                    'total_return': float(total_return),
                    'start_price': float(first_prices[asset]),
                    'end_price': float(last_prices[asset]),
                    'start_date': prices_df.index[0].strftime('%Y-%m-%d'),
                    'end_date': prices_df.index[-1].strftime('%Y-%m-%d')
                }
        
        return performance_data