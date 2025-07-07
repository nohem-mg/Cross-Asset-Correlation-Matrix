from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime
import json

from config import Config
from data_fetcher import DataFetcher
from correlation_calc import CorrelationCalculator

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=Config.CORS_ORIGINS)

# Initialize components
data_fetcher = DataFetcher()
calc = CorrelationCalculator()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/assets', methods=['GET'])
def get_available_assets():
    """Get list of available assets"""
    return jsonify({
        'crypto': [{'symbol': k, 'name': v} for k, v in Config.CRYPTO_ASSETS.items()],
        'stocks': [{'symbol': k, 'name': v} for k, v in Config.STOCK_ASSETS.items()],
        'etfs': [{'symbol': k, 'name': v} for k, v in Config.ETF_ASSETS.items()],
        'commodities': [{'symbol': k, 'name': v} for k, v in Config.COMMODITY_ASSETS.items()]
    })

@app.route('/api/periods', methods=['GET'])
def get_time_periods():
    """Get available time periods"""
    return jsonify({
        period: info['label'] 
        for period, info in Config.TIME_PERIODS.items()
    })

@app.route('/api/correlation', methods=['POST'])
def calculate_correlation():
    """Calculate correlation matrix for selected assets"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'assets' not in data or 'period' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        assets = data['assets']
        period = data['period']
        correlation_method = data.get('correlation_method', 'pearson')
        returns_method = data.get('returns_method', 'log')
        
        # Validate period
        if period not in Config.TIME_PERIODS:
            return jsonify({'error': 'Invalid time period'}), 400
        
        # Fetch data
        prices_df = data_fetcher.fetch_mixed_assets(assets, period)
        
        if prices_df.empty:
            return jsonify({'error': 'No data available for selected assets'}), 404
        
        # Calculate returns
        returns_df = calc.calculate_returns(prices_df, method=returns_method)
        
        # Calculate correlation matrix
        corr_matrix = calc.calculate_correlation_matrix(returns_df, method=correlation_method)
        
        # Calculate additional metrics
        diversification_score = calc.calculate_diversification_score(corr_matrix)
        statistics = calc.calculate_statistics(returns_df)
        
        # Find highly correlated pairs
        positive_pairs = calc.find_correlated_pairs(corr_matrix, threshold=0.7, correlation_type='positive')
        negative_pairs = calc.find_correlated_pairs(corr_matrix, threshold=0.7, correlation_type='negative')
        
        # Calculate beta if SPY is included
        betas = {}
        if 'SPY' in returns_df.columns:
            betas = calc.calculate_beta(returns_df, 'SPY')
        
        # Prepare response
        response = {
            'correlation_matrix': corr_matrix.to_dict(),
            'assets': corr_matrix.columns.tolist(),
            'diversification_score': diversification_score,
            'statistics': statistics,
            'highly_correlated': {
                'positive': positive_pairs[:10],  # Top 10
                'negative': negative_pairs[:10]
            },
            'betas': betas,
            'period': period,
            'data_points': len(returns_df),
            'start_date': prices_df.index[0].strftime('%Y-%m-%d'),
            'end_date': prices_df.index[-1].strftime('%Y-%m-%d')
        }
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Error calculating correlation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prices', methods=['POST'])
def get_latest_prices():
    """Get latest prices for selected assets"""
    try:
        data = request.get_json()
        
        if not data or 'assets' not in data:
            return jsonify({'error': 'Missing assets parameter'}), 400
        
        prices = data_fetcher.get_latest_prices(data['assets'])
        
        return jsonify({
            'prices': prices,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error fetching prices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rolling-correlation', methods=['POST'])
def calculate_rolling_correlation():
    """Calculate rolling correlation between two assets"""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['asset1', 'asset2', 'period']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Extract parameters
        asset1 = data['asset1']
        asset2 = data['asset2']
        period = data['period']
        window = data.get('window', 30)
        
        # Determine asset types
        assets = {'crypto': [], 'stocks': [], 'etfs': [], 'commodities': []}
        
        for asset in [asset1, asset2]:
            if asset in Config.CRYPTO_ASSETS:
                assets['crypto'].append(asset)
            elif asset in Config.STOCK_ASSETS:
                assets['stocks'].append(asset)
            elif asset in Config.ETF_ASSETS:
                assets['etfs'].append(asset)
            elif asset in Config.COMMODITY_ASSETS:
                assets['commodities'].append(asset)
        
        # Fetch data
        prices_df = data_fetcher.fetch_mixed_assets(assets, period)
        
        if prices_df.empty or asset1 not in prices_df.columns or asset2 not in prices_df.columns:
            return jsonify({'error': 'Data not available for selected assets'}), 404
        
        # Calculate returns
        returns_df = calc.calculate_returns(prices_df)
        
        # Calculate rolling correlation
        rolling_corr = calc.calculate_rolling_correlation(
            returns_df, 
            window=window, 
            asset1=asset1, 
            asset2=asset2
        )
        
        # Prepare data for response
        dates = rolling_corr.index.strftime('%Y-%m-%d').tolist()
        values = rolling_corr.iloc[:, 0].fillna(0).tolist()
        
        return jsonify({
            'dates': dates,
            'values': values,
            'asset1': asset1,
            'asset2': asset2,
            'window': window,
            'current_correlation': values[-1] if values else 0
        })
        
    except Exception as e:
        app.logger.error(f"Error calculating rolling correlation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_data():
    """Export correlation data as CSV"""
    try:
        data = request.get_json()
        
        if not data or 'correlation_matrix' not in data:
            return jsonify({'error': 'Missing correlation matrix'}), 400
        
        # Convert correlation matrix to DataFrame
        corr_df = pd.DataFrame(data['correlation_matrix'])
        
        # Convert to CSV
        csv_data = corr_df.to_csv()
        
        return jsonify({
            'csv': csv_data,
            'filename': f"correlation_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        })
        
    except Exception as e:
        app.logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, port=5000)