// Chart Module for data visualization
const ChartModule = {
    // Plotly dark theme configuration
    darkTheme: {
        plot_bgcolor: '#0f172a',
        paper_bgcolor: '#1e293b',
        font: {
            color: '#f1f5f9'
        },
        xaxis: {
            gridcolor: '#334155',
            zerolinecolor: '#334155'
        },
        yaxis: {
            gridcolor: '#334155',
            zerolinecolor: '#334155'
        }
    },
    
    // Create correlation heatmap
    createCorrelationHeatmap(correlationData, assets, assetNames = {}) {
        const container = document.getElementById('correlation-heatmap');
        
        // Créer les labels d'affichage (noms complets)
        const displayLabels = assets.map(asset => assetNames[asset] || asset);
        
        // Prepare data for heatmap
        const zValues = [];
        const annotations = [];
        
        for (let i = 0; i < assets.length; i++) {
            const row = [];
            for (let j = 0; j < assets.length; j++) {
                const value = correlationData[assets[i]][assets[j]];
                row.push(value);
                
                // Add text annotations - utiliser les noms pour les positions
                annotations.push({
                    x: displayLabels[j],
                    y: displayLabels[i],
                    text: value.toFixed(2),
                    showarrow: false,
                    font: {
                        size: 12,
                        color: Math.abs(value) > 0.5 ? 'white' : '#94a3b8'
                    }
                });
            }
            zValues.push(row);
        }
        
        const data = [{
            type: 'heatmap',
            x: displayLabels,  // Utiliser les noms au lieu des symboles
            y: displayLabels,  // Utiliser les noms au lieu des symboles
            z: zValues,
            colorscale: [
                [0, '#ef4444'],      // Strong negative (red)
                [0.25, '#f59e0b'],   // Weak negative (orange)
                [0.5, '#6b7280'],    // Neutral (gray)
                [0.75, '#10b981'],   // Weak positive (green)
                [1, '#059669']       // Strong positive (dark green)
            ],
            zmin: -1,
            zmax: 1,
            colorbar: {
                title: 'Corrélation',
                thickness: 20,
                len: 0.7
            }
        }];
        
        const layout = {
            title: {
                text: 'Matrice de Corrélation',
                font: { size: 18 }
            },
            xaxis: {
                side: 'bottom',
                tickangle: -45
            },
            yaxis: {
                autorange: 'reversed'
            },
            annotations: annotations,
            ...this.darkTheme,
            margin: {
                l: 100,
                r: 50,
                b: 100,
                t: 80,
                pad: 4
            }
        };
        
        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'resetScale2d']
        };
        
        Plotly.newPlot(container, data, layout, config);
    },
    

    
    // Create statistics table
    createStatisticsTable(statistics, betas, assetNames = {}) {
        const container = document.getElementById('asset-statistics');
        
        // Create table HTML
        let tableHTML = `
            <div class="stats-table-container">
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Actif</th>
                            <th>Rendement Moyen</th>
                            <th>Volatilité</th>
                            <th>Ratio de Sharpe</th>
                            <th>Beta (vs SPY)</th>
                            <th>Skewness</th>
                            <th>Kurtosis</th>
                            <th>Jours Positifs</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        for (const [asset, stats] of Object.entries(statistics)) {
            const beta = betas[asset] || '-';
            const positivePercentage = ((stats.positive_days / stats.total_days) * 100).toFixed(1);
            const displayName = assetNames[asset] || asset;  // Utiliser le nom complet si disponible
            
            tableHTML += `
                <tr>
                    <td><strong>${displayName}</strong></td>
                    <td class="${stats.mean_return > 0 ? 'positive' : 'negative'}">
                        ${(stats.mean_return * 100).toFixed(3)}%
                    </td>
                    <td>${(stats.volatility * 100).toFixed(3)}%</td>
                    <td class="${stats.sharpe_ratio > 0 ? 'positive' : 'negative'}">
                        ${stats.sharpe_ratio.toFixed(2)}
                    </td>
                    <td>${typeof beta === 'number' ? beta.toFixed(2) : beta}</td>
                    <td>${stats.skewness.toFixed(2)}</td>
                    <td>${stats.kurtosis.toFixed(2)}</td>
                    <td>${positivePercentage}% (${stats.positive_days}/${stats.total_days})</td>
                </tr>
            `;
        }
        
        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHTML;
        
        // Add CSS classes for positive/negative values
        const style = document.createElement('style');
        style.textContent = `
            .positive { color: #10b981; }
            .negative { color: #ef4444; }
            .stats-table-container { overflow-x: auto; }
        `;
        document.head.appendChild(style);
    },
    
    // Create performance comparison chart
    createPerformanceComparison(performanceData, assetNames = {}, period = '') {
        const container = document.getElementById('performance-comparison');
        
        // Vider le container d'abord
        container.innerHTML = '';
        
        if (!performanceData || Object.keys(performanceData).length === 0) {
            container.innerHTML = '<p class="no-data">Aucune donnée de performance disponible</p>';
            return;
        }
        
        // Trier les actifs par performance (du moins performant au plus performant pour avoir le meilleur à droite)
        const sortedAssets = Object.entries(performanceData)
            .sort((a, b) => a[1].total_return - b[1].total_return);
        
        const assets = sortedAssets.map(([asset, _]) => asset);
        const returns = sortedAssets.map(([_, data]) => data.total_return);
        const displayNames = assets.map(asset => assetNames[asset] || asset);
        
        // Couleurs basées sur la performance (vert pour positif, rouge pour négatif)
        const colors = returns.map(ret => ret >= 0 ? '#10b981' : '#ef4444');
        
        // Calculer l'échelle dynamique basée sur les performances réelles
        const minReturn = Math.min(...returns);
        const maxReturn = Math.max(...returns);
        
        // Ajouter des marges de 10% de chaque côté
        const range = maxReturn - minReturn;
        const margin = Math.max(range * 0.1, 5); // Minimum 5% de marge
        
        let yMin = minReturn - margin;
        let yMax = maxReturn + margin;
        
        // S'assurer que 0 est toujours visible si on a des valeurs positives et négatives
        if (minReturn < 0 && maxReturn > 0) {
            // On garde l'échelle actuelle qui inclut déjà 0
        } else if (minReturn >= 0) {
            // Toutes valeurs positives : commencer à 0 ou légèrement en dessous
            yMin = Math.min(0, yMin);
        } else if (maxReturn <= 0) {
            // Toutes valeurs négatives : finir à 0 ou légèrement au dessus
            yMax = Math.max(0, yMax);
        }
        
        const data = [{
            type: 'bar',
            x: displayNames,
            y: returns,
            marker: {
                color: colors,
                line: {
                    color: 'rgba(255,255,255,0.2)',
                    width: 1
                }
            },
            text: returns.map(ret => `${ret >= 0 ? '+' : ''}${ret.toFixed(2)}%`),
            textposition: 'outside',
            textfont: {
                color: '#f1f5f9',
                size: 12
            }
        }];
        
        // Convertir la période en français pour l'affichage
        const periodLabels = {
            '7d': '7 jours',
            '30d': '30 jours', 
            '90d': '90 jours',
            '180d': '6 mois',
            '1y': '1 an',
            'ytd': 'Depuis début d\'année'
        };
        const periodLabel = periodLabels[period] || period || 'période sélectionnée'; // Fallback
        
        // Créer un div pour le graphique
        const chartDiv = document.createElement('div');
        chartDiv.id = 'performance-chart';
        chartDiv.style.height = '400px';
        container.appendChild(chartDiv);
        
        const layout = {
            ...this.darkTheme,
            title: {
                text: `Performance sur ${periodLabel}`,
                font: { size: 16, color: '#f1f5f9' }
            },
            xaxis: {
                title: 'Actifs',
                tickangle: -45,
                automargin: true,
                tickfont: {
                    size: 12,
                    color: '#f1f5f9'
                },
                titlefont: {
                    size: 14,
                    color: '#f1f5f9'
                }
            },
            yaxis: {
                title: 'Performance (%)',
                zeroline: true,
                zerolinecolor: '#f59e0b',
                zerolinewidth: 3,
                range: [yMin, yMax],
                automargin: true,
                tickfont: {
                    size: 14,
                    color: '#f1f5f9'
                },
                titlefont: {
                    size: 14,
                    color: '#f1f5f9'
                },
                ticksuffix: '%',
                gridcolor: '#334155',
                gridwidth: 1
            },
            margin: {
                l: 80,
                r: 40,
                b: 120,
                t: 80,
                pad: 4
            },
            showlegend: false,
            autosize: true
        };
        
        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'resetScale2d']
        };
        
        // Créer le graphique
        Plotly.newPlot(chartDiv, data, layout, config);
        
        // Ajouter un tableau récapitulatif sous le graphique
        const tableContainer = document.createElement('div');
        tableContainer.style.marginTop = '20px';
        
        // Trier par performance décroissante pour le tableau (meilleur en premier)
        const sortedForTable = Object.entries(performanceData)
            .sort((a, b) => b[1].total_return - a[1].total_return);
        
        let tableHTML = `
            <div class="performance-table-container">
                <h4 style="color: var(--text-secondary); margin-bottom: 15px; font-size: 1rem;">
                    📊 Classement sur ${periodLabel}
                </h4>
                <table class="performance-table">
                    <thead>
                        <tr>
                            <th>Rang</th>
                            <th>Actif</th>
                            <th>Performance</th>
                            <th>Prix Initial</th>
                            <th>Prix Final</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        sortedForTable.forEach(([asset, data], index) => {
            const displayName = assetNames[asset] || asset;
            const performanceClass = data.total_return >= 0 ? 'positive' : 'negative';
            
            // Ajouter des médailles pour les 3 premiers
            let rankDisplay = `${index + 1}`;
            if (index === 0) rankDisplay = '🥇 1';
            else if (index === 1) rankDisplay = '🥈 2';
            else if (index === 2) rankDisplay = '🥉 3';
            
            tableHTML += `
                <tr>
                    <td><strong>${rankDisplay}</strong></td>
                    <td><strong>${displayName}</strong></td>
                    <td class="${performanceClass}">
                        ${data.total_return >= 0 ? '+' : ''}${data.total_return.toFixed(2)}%
                    </td>
                    <td>${data.start_price.toFixed(4)}</td>
                    <td>${data.end_price.toFixed(4)}</td>
                </tr>
            `;
        });
        
        tableHTML += `
                    </tbody>
                </table>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 10px; text-align: center;">
                    Du ${sortedForTable[0][1].start_date} au ${sortedForTable[0][1].end_date}
                </p>
            </div>
        `;
        
        tableContainer.innerHTML = tableHTML;
        container.appendChild(tableContainer);
        
        // Ajouter les styles CSS pour le tableau
        const style = document.createElement('style');
        style.textContent = `
            .performance-table-container { 
                overflow-x: auto; 
                margin-top: 20px;
            }
            .performance-table {
                width: 100%;
                border-collapse: collapse;
                background: var(--dark-bg);
                border-radius: 8px;
                overflow: hidden;
            }
            .performance-table th,
            .performance-table td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid var(--border-color);
            }
            .performance-table th {
                background: var(--card-bg);
                font-weight: 600;
                color: var(--text-secondary);
            }
            .performance-table tr:hover {
                background: rgba(37, 99, 235, 0.05);
            }
            .performance-table .positive { color: #10b981; font-weight: 600; }
            .performance-table .negative { color: #ef4444; font-weight: 600; }
        `;
        document.head.appendChild(style);
    },
    
    // Display correlation pairs
    displayCorrelationPairs(positivePairs, negativePairs, assetNames = {}) {
        const positiveContainer = document.getElementById('positive-pairs');
        const negativeContainer = document.getElementById('negative-pairs');
        
        // Display positive correlations
        if (positivePairs.length > 0) {
            positiveContainer.innerHTML = positivePairs.map(pair => {
                const name1 = assetNames[pair.asset1] || pair.asset1;
                const name2 = assetNames[pair.asset2] || pair.asset2;
                return `
                    <div class="pair-item">
                        <span class="pair-assets">${name1} - ${name2}</span>
                        <span class="pair-correlation positive">${pair.correlation.toFixed(3)}</span>
                    </div>
                `;
            }).join('');
        } else {
            positiveContainer.innerHTML = '<p class="no-data">Aucune paire fortement corrélée positivement</p>';
        }
        
        // Display negative correlations
        if (negativePairs.length > 0) {
            negativeContainer.innerHTML = negativePairs.map(pair => {
                const name1 = assetNames[pair.asset1] || pair.asset1;
                const name2 = assetNames[pair.asset2] || pair.asset2;
                return `
                    <div class="pair-item">
                        <span class="pair-assets">${name1} - ${name2}</span>
                        <span class="pair-correlation negative">${pair.correlation.toFixed(3)}</span>
                    </div>
                `;
            }).join('');
        } else {
            negativeContainer.innerHTML = '<p class="no-data">Aucune paire fortement corrélée négativement</p>';
        }
    },
    
    // Update metrics display
    updateMetrics(data) {
        // Diversification score
        const scoreElement = document.getElementById('diversification-score');
        const score = data.diversification_score;
        scoreElement.textContent = score.toFixed(3);
        
        // Add color based on score
        if (score > 0.7) {
            scoreElement.style.color = '#10b981';
        } else if (score > 0.4) {
            scoreElement.style.color = '#f59e0b';
        } else {
            scoreElement.style.color = '#ef4444';
        }
        
        // Data points
        document.getElementById('data-points').textContent = data.data_points;
        
        // Period range - format the dates nicely
        const startDate = new Date(data.start_date).toLocaleDateString('fr-FR');
        const endDate = new Date(data.end_date).toLocaleDateString('fr-FR');
        document.getElementById('period-range').textContent = `${startDate} - ${endDate}`;
    }
};

// Export for use in other modules
window.ChartModule = ChartModule;