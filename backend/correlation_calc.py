import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats

class CorrelationCalculator:
    
    @staticmethod
    def calculate_returns(prices_df: pd.DataFrame, method: str = 'log') -> pd.DataFrame:
        """Calculate returns from price data"""
        if method == 'log':
            # Log returns
            returns = np.log(prices_df / prices_df.shift(1))
        else:
            # Simple returns
            returns = prices_df.pct_change()
        
        # Remove first row (NaN)
        returns = returns.dropna()
        return returns
    
    @staticmethod
    def calculate_correlation_matrix(returns_df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
        """Calculate correlation matrix"""
        if method == 'pearson':
            corr_matrix = returns_df.corr(method='pearson')
        elif method == 'spearman':
            corr_matrix = returns_df.corr(method='spearman')
        elif method == 'kendall':
            corr_matrix = returns_df.corr(method='kendall')
        else:
            raise ValueError(f"Unknown correlation method: {method}")
        
        return corr_matrix
    
    @staticmethod
    def calculate_rolling_correlation(returns_df: pd.DataFrame, 
                                    window: int = 30,
                                    asset1: Optional[str] = None,
                                    asset2: Optional[str] = None) -> pd.DataFrame:
        """Calculate rolling correlation between assets"""
        if asset1 and asset2:
            if asset1 in returns_df.columns and asset2 in returns_df.columns:
                rolling_corr = returns_df[asset1].rolling(window).corr(returns_df[asset2])
                return pd.DataFrame({f'{asset1}_vs_{asset2}': rolling_corr})
        
        # Calculate all pairwise rolling correlations
        assets = returns_df.columns.tolist()
        rolling_corrs = {}
        
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets[i+1:], i+1):
                corr_series = returns_df[asset1].rolling(window).corr(returns_df[asset2])
                rolling_corrs[f'{asset1}_vs_{asset2}'] = corr_series
        
        return pd.DataFrame(rolling_corrs)
    
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
        """Calculate various statistics for each asset"""
        stats = {}
        
        for asset in returns_df.columns:
            asset_returns = returns_df[asset].dropna()
            
            stats[asset] = {
                'mean_return': float(asset_returns.mean()),
                'volatility': float(asset_returns.std()),
                'sharpe_ratio': float(asset_returns.mean() / asset_returns.std() * np.sqrt(252)) if asset_returns.std() > 0 else 0,
                'skewness': float(stats.skew(asset_returns)),
                'kurtosis': float(stats.kurtosis(asset_returns)),
                'max_return': float(asset_returns.max()),
                'min_return': float(asset_returns.min()),
                'positive_days': int((asset_returns > 0).sum()),
                'negative_days': int((asset_returns < 0).sum()),
                'total_days': len(asset_returns)
            }
        
        return stats
    
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