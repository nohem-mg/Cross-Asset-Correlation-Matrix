// API Module for handling backend communication
const API = {
    // Base URL for API endpoints - Auto-detect based on current location
    baseURL: (() => {
        // Pour le développement, on utilise le port 5000
        const host = window.location.hostname || 'localhost';
        return `http://${host}:5000/api`;
    })(),
    
    // Helper function for making API requests
    async request(endpoint, options = {}) {
        try {
            console.log(`Making request to: ${this.baseURL}${endpoint}`);
            
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    // Get available assets
    async getAssets() {
        return this.request('/assets');
    },
    
    // Get available time periods
    async getPeriods() {
        return this.request('/periods');
    },
    
    // Calculate correlation matrix
    async calculateCorrelation(assets, period, correlationMethod = 'pearson', returnsMethod = 'log') {
        return this.request('/correlation', {
            method: 'POST',
            body: JSON.stringify({
                assets,
                period,
                correlation_method: correlationMethod,
                returns_method: returnsMethod
            })
        });
    },
    
    // Get latest prices
    async getLatestPrices(assets) {
        return this.request('/prices', {
            method: 'POST',
            body: JSON.stringify({ assets })
        });
    },
    
    // Search for assets in Yahoo Finance and CoinGecko
    async searchAssets(query) {
        return this.request('/search-assets', {
            method: 'POST',
            body: JSON.stringify({ query })
        });
    },
    
    // Add a custom asset
    async addCustomAsset(symbol, name, category, source) {
        return this.request('/add-custom-asset', {
            method: 'POST',
            body: JSON.stringify({
                symbol,
                name,
                category,
                source
            })
        });
    },

    // Export correlation data
    async exportData(correlationMatrix) {
        return this.request('/export', {
            method: 'POST',
            body: JSON.stringify({
                correlation_matrix: correlationMatrix
            })
        });
    },
    
    // Health check
    async healthCheck() {
        return this.request('/health');
    }
};

// Log the API base URL for debugging
console.log('API Base URL:', API.baseURL);

// Export for use in other modules
window.API = API;