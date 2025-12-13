from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime
import json
import logging

from config import Config
from data_fetcher import DataFetcher
from correlation_calc import CorrelationCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=Config.CORS_ORIGINS)

# Initialize components
data_fetcher = DataFetcher()
calc = CorrelationCalculator()

@app.before_request
def log_request_info():
    """Log incoming requests for debugging"""
    if request.endpoint != 'health_check':
        logger.debug(f"Request: {request.method} {request.path}")

@app.errorhandler(Exception)
def handle_exception(e):
    """Global error handler"""
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify({'error': 'Une erreur interne est survenue'}), 500

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
    def get_display_name(symbol, fallback_name):
        return Config.DISPLAY_NAMES.get(symbol, fallback_name)
    
    return jsonify({
        'crypto': [{'symbol': Config.DISPLAY_SYMBOLS.get(k, k), 'name': get_display_name(k, v), 'technical_symbol': k} for k, v in Config.CRYPTO_ASSETS.items()],
        'stocks': [{'symbol': Config.DISPLAY_SYMBOLS.get(k, k), 'name': get_display_name(k, v), 'technical_symbol': k} for k, v in Config.STOCK_ASSETS.items()],
        'etfs': [{'symbol': Config.DISPLAY_SYMBOLS.get(k, k), 'name': get_display_name(k, v), 'technical_symbol': k} for k, v in Config.ETF_ASSETS.items()],
        'commodities': [{'symbol': Config.DISPLAY_SYMBOLS.get(k, k), 'name': get_display_name(k, v), 'technical_symbol': k} for k, v in Config.COMMODITY_ASSETS.items()]
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
            return jsonify({'error': 'Paramètres requis manquants (assets, period)'}), 400

        assets = data['assets']
        period = data['period']
        correlation_method = data.get('correlation_method', 'pearson')
        returns_method = data.get('returns_method', 'log')

        # Validate that at least some assets are selected
        total_assets = sum(len(v) for v in assets.values() if isinstance(v, list))
        if total_assets < 2:
            return jsonify({'error': 'Veuillez sélectionner au moins 2 actifs'}), 400

        # Validate period
        if period not in Config.TIME_PERIODS:
            return jsonify({'error': f'Période invalide. Choix: {list(Config.TIME_PERIODS.keys())}'}), 400

        logger.info(f"Calculating correlation for {total_assets} assets over {period}")

        # Fetch data
        prices_df = data_fetcher.fetch_mixed_assets(assets, period)

        if prices_df.empty:
            return jsonify({
                'error': 'Aucune donnée disponible pour les actifs sélectionnés. '
                         'Vérifiez que les symboles sont corrects et réessayez.'
            }), 404

        if len(prices_df.columns) < 2:
            return jsonify({
                'error': f'Données insuffisantes. Seulement {len(prices_df.columns)} actif(s) avec des données.'
            }), 400

        # Calculate returns
        returns_df = calc.calculate_returns(prices_df, method=returns_method)

        if returns_df.empty or len(returns_df) < 5:
            return jsonify({
                'error': f'Données insuffisantes pour calculer les corrélations. '
                         f'Seulement {len(returns_df)} points de données disponibles.'
            }), 400

        # Calculate correlation matrix
        corr_matrix = calc.calculate_correlation_matrix(returns_df, method=correlation_method)

        if corr_matrix.empty:
            return jsonify({'error': 'Impossible de calculer la matrice de corrélation'}), 500

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

        # Calculate performance comparison
        performance_comparison = calc.calculate_performance_comparison(prices_df)

        # Create mapping of technical symbols to names
        asset_names = {}
        for technical_symbol in corr_matrix.columns:
            # Utiliser DISPLAY_NAMES si disponible, sinon fallback vers les dictionnaires d'actifs
            if technical_symbol in Config.DISPLAY_NAMES:
                asset_names[technical_symbol] = Config.DISPLAY_NAMES[technical_symbol]
            elif technical_symbol in Config.CRYPTO_ASSETS:
                asset_names[technical_symbol] = Config.CRYPTO_ASSETS[technical_symbol]
            elif technical_symbol in Config.STOCK_ASSETS:
                asset_names[technical_symbol] = Config.STOCK_ASSETS[technical_symbol]
            elif technical_symbol in Config.ETF_ASSETS:
                asset_names[technical_symbol] = Config.ETF_ASSETS[technical_symbol]
            elif technical_symbol in Config.COMMODITY_ASSETS:
                asset_names[technical_symbol] = Config.COMMODITY_ASSETS[technical_symbol]
            else:
                asset_names[technical_symbol] = technical_symbol  # fallback

        # Prepare response
        response = {
            'correlation_matrix': corr_matrix.to_dict(),
            'assets': corr_matrix.columns.tolist(),
            'asset_names': asset_names,
            'diversification_score': diversification_score,
            'statistics': statistics,
            'performance_comparison': performance_comparison,
            'highly_correlated': {
                'positive': positive_pairs[:10],
                'negative': negative_pairs[:10]
            },
            'betas': betas,
            'period': period,
            'data_points': len(returns_df),
            'start_date': prices_df.index[0].strftime('%Y-%m-%d'),
            'end_date': prices_df.index[-1].strftime('%Y-%m-%d')
        }

        logger.info(f"Correlation calculated successfully: {len(corr_matrix)} assets, {len(returns_df)} data points")
        return jsonify(response)

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error calculating correlation: {str(e)}", exc_info=True)
        return jsonify({'error': f'Erreur lors du calcul: {str(e)}'}), 500

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

@app.route('/api/search-assets', methods=['POST'])
def search_assets():
    """Search for assets in Yahoo Finance and CoinGecko"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing search query'}), 400
        
        query = data['query'].strip()
        
        if len(query) < 2:
            return jsonify({'error': 'Query too short'}), 400
        
        results = data_fetcher.search_assets(query)
        
        return jsonify({
            'results': results,
            'query': query
        })
        
    except Exception as e:
        app.logger.error(f"Error searching assets: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-custom-asset', methods=['POST'])
def add_custom_asset():
    """Add a custom asset temporarily to the session"""
    try:
        data = request.get_json()
        
        required_fields = ['symbol', 'name', 'category', 'source']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        symbol = data['symbol'].upper().strip()
        name = data['name'].strip()
        category = data['category'].strip()
        source = data['source'].strip()  # 'yahoo' or 'coingecko'
        
        # Validate category
        valid_categories = ['crypto', 'stocks', 'etfs', 'commodities']
        if category not in valid_categories:
            return jsonify({'error': f'Invalid category. Must be one of: {valid_categories}'}), 400
        
        # Validate the asset exists and can be fetched
        validation_result = data_fetcher.validate_asset(symbol, source)
        
        if not validation_result['valid']:
            return jsonify({'error': validation_result['error']}), 400
        
        return jsonify({
            'success': True,
            'asset': {
                'symbol': symbol,
                'name': name,
                'technical_symbol': symbol,
                'category': category,
                'source': source,
                'custom': True
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error adding custom asset: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, port=5000)