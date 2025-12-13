// API Module for handling backend communication
const API = {
    // Base URL for API endpoints - Auto-detect based on environment
    baseURL: (() => {
        // Check for custom API URL (for production deployments)
        // You can set this in a config.js file or as a global variable
        if (window.API_BASE_URL) {
            return window.API_BASE_URL;
        }

        const hostname = window.location.hostname;

        // Production detection - common deployment platforms
        const isProduction = (
            hostname !== 'localhost' &&
            hostname !== '127.0.0.1' &&
            !hostname.includes('192.168.') &&
            !hostname.includes('10.0.')
        );

        if (isProduction) {
            // In production, the backend should be deployed separately
            // Options:
            // 1. Same domain with /api prefix (if using reverse proxy)
            // 2. Separate backend URL (configure via window.API_BASE_URL)

            // Try same origin first (useful if backend is proxied)
            return `${window.location.origin}/api`;
        }

        // Development mode - use localhost with Flask port
        return 'http://localhost:5000/api';
    })(),

    // Request timeout in milliseconds
    timeout: 60000,

    // Retry configuration
    maxRetries: 2,
    retryDelay: 1000,

    // Helper function for making API requests with retry logic
    async request(endpoint, options = {}, retryCount = 0) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            console.log(`Making request to: ${this.baseURL}${endpoint}`);

            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                signal: controller.signal,
                ...options
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                let errorMessage;
                try {
                    const error = await response.json();
                    errorMessage = error.error || `Erreur HTTP ${response.status}`;
                } catch {
                    errorMessage = `Erreur HTTP ${response.status}`;
                }
                throw new Error(errorMessage);
            }

            return await response.json();

        } catch (error) {
            clearTimeout(timeoutId);

            // Handle abort/timeout
            if (error.name === 'AbortError') {
                throw new Error('La requête a expiré. Le serveur met trop de temps à répondre.');
            }

            // Handle network errors with retry
            if (error.message === 'Failed to fetch' && retryCount < this.maxRetries) {
                console.warn(`Request failed, retrying (${retryCount + 1}/${this.maxRetries})...`);
                await new Promise(resolve => setTimeout(resolve, this.retryDelay * (retryCount + 1)));
                return this.request(endpoint, options, retryCount + 1);
            }

            // Handle connection refused
            if (error.message === 'Failed to fetch') {
                throw new Error('Impossible de se connecter au serveur. Vérifiez que le backend est démarré.');
            }

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