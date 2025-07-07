// Main Application Module
const App = {
    // State management
    state: {
        availableAssets: {},
        selectedAssets: {
            crypto: [],
            stocks: [],
            etfs: [],
            commodities: []
        },
        currentData: null,
        loading: false
    },
    
    // Initialize the application
    async init() {
        console.log('Initializing application...');
        
        // Check API health
        try {
            await API.healthCheck();
            console.log('API is healthy');
        } catch (error) {
            this.showError('Impossible de se connecter au serveur. Assurez-vous que le backend est démarré.');
            return;
        }
        
        // Load available assets
        await this.loadAssets();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize with some default selections
        this.setDefaultSelections();
    },
    
    // Load available assets from API
    async loadAssets() {
        try {
            const assets = await API.getAssets();
            this.state.availableAssets = assets;
            
            // Render asset grids
            this.renderAssetGrid('crypto', assets.crypto);
            this.renderAssetGrid('stocks', assets.stocks);
            this.renderAssetGrid('etfs', assets.etfs);
            this.renderAssetGrid('commodities', assets.commodities);
            
        } catch (error) {
            this.showError('Erreur lors du chargement des actifs');
            console.error(error);
        }
    },
    
    // Render asset grid for a specific category
    renderAssetGrid(category, assets) {
        const container = document.getElementById(`${category}-tab`);
        container.innerHTML = assets.map(asset => `
            <div class="asset-item" data-category="${category}" data-symbol="${asset.symbol}">
                <div>
                    <div class="symbol">${asset.symbol}</div>
                    <div class="name">${asset.name}</div>
                </div>
                <i class="fas fa-check" style="display: none; color: #10b981;"></i>
            </div>
        `).join('');
    },
    
    // Setup event listeners
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Asset selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.asset-item')) {
                this.toggleAsset(e.target.closest('.asset-item'));
            }
            
            if (e.target.classList.contains('remove-btn')) {
                const symbol = e.target.dataset.symbol;
                const category = e.target.dataset.category;
                this.removeAsset(symbol, category);
            }
        });
        
        // Calculate button
        document.getElementById('calculate-btn').addEventListener('click', () => {
            this.calculateCorrelation();
        });
        
        // Export button
        document.getElementById('export-btn').addEventListener('click', () => {
            this.exportData();
        });
        
        // Rolling correlation
        document.getElementById('rolling-calculate').addEventListener('click', () => {
            this.calculateRollingCorrelation();
        });
    },
    
    // Switch between asset tabs
    switchTab(tab) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        
        // Update tab content
        document.querySelectorAll('.asset-grid').forEach(grid => {
            grid.classList.toggle('active', grid.id === `${tab}-tab`);
        });
    },
    
    // Toggle asset selection
    toggleAsset(element) {
        const symbol = element.dataset.symbol;
        const category = element.dataset.category;
        const isSelected = element.classList.contains('selected');
        
        if (isSelected) {
            this.removeAsset(symbol, category);
        } else {
            this.addAsset(symbol, category);
        }
    },
    
    // Add asset to selection
    addAsset(symbol, category) {
        if (!this.state.selectedAssets[category].includes(symbol)) {
            this.state.selectedAssets[category].push(symbol);
            this.updateUI();
        }
    },
    
    // Remove asset from selection
    removeAsset(symbol, category) {
        const index = this.state.selectedAssets[category].indexOf(symbol);
        if (index > -1) {
            this.state.selectedAssets[category].splice(index, 1);
            this.updateUI();
        }
    },
    
    // Update UI based on current state
    updateUI() {
        // Update asset items
        document.querySelectorAll('.asset-item').forEach(item => {
            const symbol = item.dataset.symbol;
            const category = item.dataset.category;
            const isSelected = this.state.selectedAssets[category].includes(symbol);
            
            item.classList.toggle('selected', isSelected);
            item.querySelector('.fa-check').style.display = isSelected ? 'block' : 'none';
        });
        
        // Update selected list
        const selectedList = document.getElementById('selected-list');
        const allSelected = [];
        
        for (const [category, symbols] of Object.entries(this.state.selectedAssets)) {
            symbols.forEach(symbol => {
                allSelected.push({ symbol, category });
            });
        }
        
        selectedList.innerHTML = allSelected.map(item => `
            <span class="selected-tag">
                ${item.symbol}
                <i class="fas fa-times remove-btn" data-symbol="${item.symbol}" data-category="${item.category}"></i>
            </span>
        `).join('');
        
        // Update count
        document.getElementById('selected-count').textContent = allSelected.length;
        
        // Enable/disable calculate button
        document.getElementById('calculate-btn').disabled = allSelected.length < 2;
    },
    
    // Set default selections
    setDefaultSelections() {
        // Default selection for demo
        this.addAsset('BTC', 'crypto');
        this.addAsset('ETH', 'crypto');
        this.addAsset('AAPL', 'stocks');
        this.addAsset('MSFT', 'stocks');
        this.addAsset('SPY', 'etfs');
        this.addAsset('GC=F', 'commodities');
    },
    
    // Calculate correlation
    async calculateCorrelation() {
        const period = document.getElementById('period-select').value;
        const correlationMethod = document.getElementById('correlation-method').value;
        
        // Check if enough assets selected
        const totalAssets = Object.values(this.state.selectedAssets).flat().length;
        if (totalAssets < 2) {
            this.showError('Veuillez sélectionner au moins 2 actifs');
            return;
        }
        
        this.showLoading(true);
        
        try {
            // Calculate correlation
            const data = await API.calculateCorrelation(
                this.state.selectedAssets,
                period,
                correlationMethod
            );
            
            this.state.currentData = data;
            
            // Show results section
            document.getElementById('results-section').style.display = 'block';
            
            // Update visualizations
            ChartModule.createCorrelationHeatmap(data.correlation_matrix, data.assets);
            ChartModule.updateMetrics(data);
            ChartModule.displayCorrelationPairs(
                data.highly_correlated.positive,
                data.highly_correlated.negative
            );
            ChartModule.createStatisticsTable(data.statistics, data.betas);
            
            // Populate rolling correlation dropdowns
            this.populateRollingDropdowns(data.assets);
            
            // Enable export button
            document.getElementById('export-btn').disabled = false;
            
            // Scroll to results
            document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            this.showError(`Erreur lors du calcul: ${error.message}`);
            console.error(error);
        } finally {
            this.showLoading(false);
        }
    },
    
    // Populate rolling correlation dropdowns
    populateRollingDropdowns(assets) {
        const select1 = document.getElementById('rolling-asset1');
        const select2 = document.getElementById('rolling-asset2');
        
        const options = assets.map(asset => `<option value="${asset}">${asset}</option>`).join('');
        
        select1.innerHTML = options;
        select2.innerHTML = options;
        
        // Select different assets by default
        if (assets.length >= 2) {
            select2.selectedIndex = 1;
        }
    },
    
    // Calculate rolling correlation
    async calculateRollingCorrelation() {
        const asset1 = document.getElementById('rolling-asset1').value;
        const asset2 = document.getElementById('rolling-asset2').value;
        const period = document.getElementById('period-select').value;
        
        if (asset1 === asset2) {
            this.showError('Veuillez sélectionner deux actifs différents');
            return;
        }
        
        this.showLoading(true);
        
        try {
            const data = await API.calculateRollingCorrelation(asset1, asset2, period);
            ChartModule.createRollingCorrelationChart(data.dates, data.values, asset1, asset2);
        } catch (error) {
            this.showError(`Erreur lors du calcul: ${error.message}`);
            console.error(error);
        } finally {
            this.showLoading(false);
        }
    },
    
    // Export data
    async exportData() {
        if (!this.state.currentData) return;
        
        try {
            const exportData = await API.exportData(this.state.currentData.correlation_matrix);
            
            // Create download link
            const blob = new Blob([exportData.csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = exportData.filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showSuccess('Données exportées avec succès');
        } catch (error) {
            this.showError('Erreur lors de l\'export');
            console.error(error);
        }
    },
    
    // Show/hide loading spinner
    showLoading(show) {
        document.getElementById('loading').style.display = show ? 'block' : 'none';
        this.state.loading = show;
    },
    
    // Show error message
    showError(message) {
        // Simple alert for now, can be replaced with a better notification system
        alert(`Erreur: ${message}`);
    },
    
    // Show success message
    showSuccess(message) {
        // Simple alert for now
        alert(message);
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});