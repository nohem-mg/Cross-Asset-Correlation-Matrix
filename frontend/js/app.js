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
        customAssets: {
            crypto: [],
            stocks: [],
            etfs: [],
            commodities: []
        },
        currentData: null,
        loading: false,
        displayToTechnicalMapping: {} // Mapping symbole affiché -> symbole technique
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
            
            // Créer le mapping symbole affiché -> symbole technique
            this.state.displayToTechnicalMapping = {};
            for (const [category, assetList] of Object.entries(assets)) {
                assetList.forEach(asset => {
                    this.state.displayToTechnicalMapping[asset.symbol] = asset.technical_symbol;
                });
            }
            
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
        
        // Combine default assets with custom assets
        const customAssets = this.state.customAssets[category] || [];
        const allAssets = [...assets, ...customAssets];
        
        container.innerHTML = allAssets.map(asset => `
            <div class="asset-item${asset.custom ? ' custom-asset' : ''}" data-category="${category}" data-symbol="${asset.symbol}" data-technical-symbol="${asset.technical_symbol}">
                <div>
                    <div class="symbol">${asset.symbol}${asset.custom ? ' <span class="custom-badge">Personnalisé</span>' : ''}</div>
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
                const displaySymbol = e.target.dataset.displaySymbol;
                const technicalSymbol = e.target.dataset.technicalSymbol;
                const category = e.target.dataset.category;
                this.removeAsset(displaySymbol, technicalSymbol, category);
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
        

        
        // Reset selection button
        document.getElementById('reset-selection-btn').addEventListener('click', () => {
            this.resetSelection();
        });
        
        // Search functionality
        document.getElementById('search-btn').addEventListener('click', () => {
            this.searchAssets();
        });
        
        document.getElementById('asset-search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchAssets();
            }
        });
        
        // Manual add functionality
        document.getElementById('add-manual-btn').addEventListener('click', () => {
            this.addManualAsset();
        });
        
        // Reset manual form functionality
        document.getElementById('reset-manual-btn').addEventListener('click', () => {
            this.resetManualForm();
        });
        
        // Search results click handler
        document.addEventListener('click', (e) => {
            if (e.target.closest('.search-result-item')) {
                this.selectSearchResult(e.target.closest('.search-result-item'));
            }
        });
    },
    
    // Switch between asset tabs
    switchTab(tab) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        
        // Update tab content - handle both asset-grid and custom-asset-section
        document.querySelectorAll('.asset-grid, .custom-asset-section').forEach(content => {
            content.classList.toggle('active', content.id === `${tab}-tab`);
        });
    },
    
    // Toggle asset selection
    toggleAsset(element) {
        const displaySymbol = element.dataset.symbol;
        const technicalSymbol = element.dataset.technicalSymbol;
        const category = element.dataset.category;
        const isSelected = element.classList.contains('selected');
        
        if (isSelected) {
            this.removeAsset(displaySymbol, technicalSymbol, category);
        } else {
            this.addAsset(displaySymbol, technicalSymbol, category);
        }
    },
    
    // Add asset to selection
    addAsset(displaySymbol, technicalSymbol, category) {
        if (!this.state.selectedAssets[category].includes(technicalSymbol)) {
            this.state.selectedAssets[category].push(technicalSymbol);
            this.updateUI();
        }
    },
    
    // Remove asset from selection
    removeAsset(displaySymbol, technicalSymbol, category) {
        const index = this.state.selectedAssets[category].indexOf(technicalSymbol);
        if (index > -1) {
            this.state.selectedAssets[category].splice(index, 1);
            this.updateUI();
        }
    },
    
    // Update UI based on current state
    updateUI() {
        // Update asset items
        document.querySelectorAll('.asset-item').forEach(item => {
            const technicalSymbol = item.dataset.technicalSymbol;
            const category = item.dataset.category;
            const isSelected = this.state.selectedAssets[category].includes(technicalSymbol);
            
            item.classList.toggle('selected', isSelected);
            item.querySelector('.fa-check').style.display = isSelected ? 'block' : 'none';
        });
        
        // Update selected list
        const selectedList = document.getElementById('selected-list');
        const allSelected = [];
        
        for (const [category, technicalSymbols] of Object.entries(this.state.selectedAssets)) {
            technicalSymbols.forEach(technicalSymbol => {
                // Trouver le symbole d'affichage correspondant
                const displaySymbol = this.findDisplaySymbol(technicalSymbol);
                allSelected.push({ displaySymbol, technicalSymbol, category });
            });
        }
        
        selectedList.innerHTML = allSelected.map(item => `
            <span class="selected-tag">
                ${item.displaySymbol}
                <i class="fas fa-times remove-btn" data-display-symbol="${item.displaySymbol}" data-technical-symbol="${item.technicalSymbol}" data-category="${item.category}"></i>
            </span>
        `).join('');
        
        // Update count
        document.getElementById('selected-count').textContent = allSelected.length;
        
        // Enable/disable calculate button
        document.getElementById('calculate-btn').disabled = allSelected.length < 2;
    },
    
    // Helper function to find display symbol from technical symbol
    findDisplaySymbol(technicalSymbol) {
        for (const [displaySymbol, techSymbol] of Object.entries(this.state.displayToTechnicalMapping)) {
            if (techSymbol === technicalSymbol) {
                return displaySymbol;
            }
        }
        return technicalSymbol; // fallback
    },
    
    // Set default selections
    setDefaultSelections() {
        // Default selection for demo - utiliser les symboles techniques
        this.addAsset('BTC', 'BTC', 'crypto');
        this.addAsset('ETH', 'ETH', 'crypto');
        this.addAsset('AAPL', 'AAPL', 'stocks');
        this.addAsset('MSFT', 'MSFT', 'stocks');
        this.addAsset('SPY', 'SPY', 'etfs');
        this.addAsset('GOLD', 'GC=F', 'commodities');
    },
    
    // Calculate correlation
    async calculateCorrelation() {
        const period = document.getElementById('period-select').value;
        const correlationMethod = 'pearson'; // Always use Pearson correlation
        
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
            ChartModule.createCorrelationHeatmap(data.correlation_matrix, data.assets, data.asset_names);
            ChartModule.updateMetrics(data);
            ChartModule.displayCorrelationPairs(
                data.highly_correlated.positive,
                data.highly_correlated.negative,
                data.asset_names
            );
            ChartModule.createStatisticsTable(data.statistics, data.betas, data.asset_names);
            
            // Create performance comparison
            ChartModule.createPerformanceComparison(data.performance_comparison, data.asset_names, period);
            

            
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
            
            this.showSuccess('Données exportées avec succès', 'Export terminé');
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
    
    // Show toast notification
    showToast(message, type = 'info', title = null, duration = 4000) {
        const container = document.getElementById('toast-container');
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        // Define icons for each type
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        // Define default titles
        const defaultTitles = {
            success: 'Succès',
            error: 'Erreur',
            warning: 'Attention',
            info: 'Information'
        };
        
        const toastTitle = title || defaultTitles[type];
        
        toast.innerHTML = `
            <i class="${icons[type]} toast-icon"></i>
            <div class="toast-content">
                <div class="toast-title">${toastTitle}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
            <div class="toast-progress"></div>
        `;
        
        // Add to container
        container.appendChild(toast);
        
        // Show toast with animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Auto-remove after duration
        const timeoutId = setTimeout(() => {
            this.removeToast(toast);
        }, duration);
        
        // Handle manual close
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            clearTimeout(timeoutId);
            this.removeToast(toast);
        });
        
        // Handle click to close
        toast.addEventListener('click', () => {
            clearTimeout(timeoutId);
            this.removeToast(toast);
        });
        
        return toast;
    },
    
    // Remove toast with animation
    removeToast(toast) {
        toast.classList.add('hide');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 400);
    },
    
    // Show error message
    showError(message, title = null) {
        this.showToast(message, 'error', title);
    },
    
    // Show success message
    showSuccess(message, title = null) {
        this.showToast(message, 'success', title);
    },
    
    // Show warning message
    showWarning(message, title = null) {
        this.showToast(message, 'warning', title);
    },
    
    // Show info message
    showInfo(message, title = null) {
        this.showToast(message, 'info', title);
    },
    
    // Search for assets
    async searchAssets() {
        const query = document.getElementById('asset-search').value.trim();
        const searchBtn = document.getElementById('search-btn');
        const resultsContainer = document.getElementById('search-results');
        
        if (query.length < 2) {
            this.showError('Veuillez entrer au moins 2 caractères');
            return;
        }
        
        // Show loading state
        searchBtn.classList.add('loading');
        resultsContainer.innerHTML = '<div class="search-loading">Recherche en cours...</div>';
        
        try {
            const response = await API.searchAssets(query);
            const results = response.results;
            
            if (results.length === 0) {
                resultsContainer.innerHTML = '<div class="search-no-results">Aucun résultat trouvé pour "' + query + '". Essayez avec le nom complet (Tesla, Apple) ou le symbole (TSLA, AAPL).</div>';
            } else {
                resultsContainer.innerHTML = results.map(result => `
                    <div class="search-result-item" data-result='${JSON.stringify(result)}'>
                        <div class="search-result-info">
                            <div class="search-result-symbol">${result.symbol}</div>
                            <div class="search-result-name">${result.name}</div>
                        </div>
                        <div class="search-result-details">
                            <span class="search-result-category">${this.getCategoryDisplayName(result.category)}</span>
                            <span class="search-result-source">${result.source === 'yahoo' ? 'Yahoo Finance' : 'CoinGecko'}</span>
                            ${result.price ? `<span class="search-result-price">$${this.formatPrice(result.price)}</span>` : ''}
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            resultsContainer.innerHTML = '<div class="search-no-results">Erreur lors de la recherche: ' + error.message + '</div>';
            console.error('Search error:', error);
        } finally {
            searchBtn.classList.remove('loading');
        }
    },
    
    // Select a search result
    selectSearchResult(element) {
        const resultData = JSON.parse(element.dataset.result);
        
        // Pre-fill the manual form
        document.getElementById('manual-symbol').value = resultData.symbol;
        document.getElementById('manual-name').value = resultData.name;
        document.getElementById('manual-category').value = resultData.category;
        document.getElementById('manual-source').value = resultData.source;
        
        // Show and highlight the manual add section with animation
        const manualSection = document.querySelector('.manual-add-section');
        manualSection.classList.add('visible');
        
        // Small delay to ensure the display transition works
        setTimeout(() => {
            manualSection.classList.add('highlighted');
        }, 100);
        
        // Update description to show selected asset
        const description = document.querySelector('.manual-description');
        description.innerHTML = `
            <i class="fas fa-check-circle" style="color: var(--secondary-color);"></i> 
            Actif sélectionné : <strong>${resultData.name} (${resultData.symbol})</strong><br>
            Vérifiez les informations ci-dessous et cliquez sur "Ajouter l'actif" pour confirmer
        `;
        
        // Scroll to manual section smoothly after animation starts
        setTimeout(() => {
            manualSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }, 200);
        
        // Clear search results
        document.getElementById('search-results').innerHTML = '';
        document.getElementById('asset-search').value = '';
        
        // Remove highlight after successful add (will be handled in addManualAsset)
        setTimeout(() => {
            manualSection.classList.remove('highlighted');
        }, 5000); // Remove highlight after 5 seconds if no action
    },
    
    // Add manual asset
    async addManualAsset() {
        const symbol = document.getElementById('manual-symbol').value.trim().toUpperCase();
        const name = document.getElementById('manual-name').value.trim();
        const category = document.getElementById('manual-category').value;
        const source = document.getElementById('manual-source').value;
        const addBtn = document.getElementById('add-manual-btn');
        
        if (!symbol || !name) {
            this.showError('Veuillez remplir le symbole et le nom');
            return;
        }
        
        // Check if asset already exists
        if (this.isAssetAlreadyAdded(symbol, category)) {
            this.showError('Cet actif est déjà ajouté');
            return;
        }
        
        addBtn.classList.add('loading');
        
        try {
            const response = await API.addCustomAsset(symbol, name, category, source);
            
            if (response.success) {
                const customAsset = response.asset;
                
                // Add to custom assets
                this.state.customAssets[category].push(customAsset);
                
                // Update display mapping
                this.state.displayToTechnicalMapping[customAsset.symbol] = customAsset.technical_symbol;
                
                // Re-render the asset grid for this category
                const defaultAssets = this.state.availableAssets[category] || [];
                this.renderAssetGrid(category, defaultAssets);
                
                // Automatically add to selection
                this.addAsset(customAsset.symbol, customAsset.technical_symbol, category);
                
                // Clear form
                document.getElementById('manual-symbol').value = '';
                document.getElementById('manual-name').value = '';
                
                // Reset description and remove highlight
                const description = document.querySelector('.manual-description');
                description.innerHTML = 'Vérifiez et modifiez les informations ci-dessous, puis cliquez sur "Ajouter l\'actif"';
                
                const manualSection = document.querySelector('.manual-add-section');
                manualSection.classList.remove('highlighted');
                manualSection.classList.remove('visible');
                
                this.showSuccess(
                    `${customAsset.name} (${customAsset.symbol}) a été ajouté avec succès dans la catégorie ${this.getCategoryDisplayName(category)}.`,
                    'Actif ajouté !'
                );
                
                // Switch to the appropriate tab to show the new asset
                this.switchTab(category);
            }
        } catch (error) {
            this.showError(`Erreur lors de l'ajout: ${error.message}`);
            console.error('Add asset error:', error);
        } finally {
            addBtn.classList.remove('loading');
        }
    },
    
    // Check if asset is already added
    isAssetAlreadyAdded(symbol, category) {
        // Check in default assets
        const defaultAssets = this.state.availableAssets[category] || [];
        const existsInDefault = defaultAssets.some(asset => 
            asset.symbol === symbol || asset.technical_symbol === symbol
        );
        
        // Check in custom assets
        const customAssets = this.state.customAssets[category] || [];
        const existsInCustom = customAssets.some(asset => 
            asset.symbol === symbol || asset.technical_symbol === symbol
        );
        
        return existsInDefault || existsInCustom;
    },
    
    // Get display name for category
    getCategoryDisplayName(category) {
        const categoryNames = {
            'crypto': 'Cryptomonnaies',
            'stocks': 'Actions',
            'etfs': 'ETFs / Indices',
            'commodities': 'Matières Premières'
        };
        return categoryNames[category] || category;
    },
    
    // Format price for display
    formatPrice(price) {
        if (price < 1) {
            return price.toFixed(4);
        } else if (price < 100) {
            return price.toFixed(2);
        } else {
            return Math.round(price).toLocaleString();
        }
    },

    // Reset manual form
    resetManualForm() {
        // Clear all form fields
        document.getElementById('manual-symbol').value = '';
        document.getElementById('manual-name').value = '';
        document.getElementById('manual-category').value = 'stocks'; // Reset to default
        document.getElementById('manual-source').value = 'yahoo'; // Reset to default
        
        // Reset description
        const description = document.querySelector('.manual-description');
        description.innerHTML = 'Vérifiez et modifiez les informations ci-dessous, puis cliquez sur "Ajouter l\'actif"';
        
        // Hide and remove highlight from manual section
        const manualSection = document.querySelector('.manual-add-section');
        manualSection.classList.remove('highlighted');
        manualSection.classList.remove('visible');
        
        // Clear search results and search input
        document.getElementById('search-results').innerHTML = '';
        document.getElementById('asset-search').value = '';
    },

    // Reset selection
    resetSelection() {
        this.state.selectedAssets = {
            crypto: [],
            stocks: [],
            etfs: [],
            commodities: []
        };
        this.updateUI();
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});