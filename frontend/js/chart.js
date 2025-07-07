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
    createCorrelationHeatmap(correlationData, assets) {
        const container = document.getElementById('correlation-heatmap');
        
        // Prepare data for heatmap
        const zValues = [];
        const annotations = [];
        
        for (let i = 0; i < assets.length; i++) {
            const row = [];
            for (let j = 0; j < assets.length; j++) {
                const value = correlationData[assets[i]][assets[j]];
                row.push(value);
                
                // Add text annotations
                annotations.push({
                    x: assets[j],
                    y: assets[i],
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
            x: assets,
            y: assets,
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
    
    // Create rolling correlation chart
    createRollingCorrelationChart(dates, values, asset1, asset2) {
        const container = document.getElementById('rolling-correlation-chart');
        
        const data = [{
            type: 'scatter',
            mode: 'lines',
            x: dates,
            y: values,
            name: `${asset1} vs ${asset2}`,
            line: {
                color: '#3b82f6',
                width: 2
            },
            fill: 'tozeroy',
            fillcolor: 'rgba(59, 130, 246, 0.1)'
        }, {
            // Add zero line
            type: 'scatter',
            mode: 'lines',
            x: [dates[0], dates[dates.length - 1]],
            y: [0, 0],
            line: {
                color: '#6b7280',
                width: 1,
                dash: 'dash'
            },
            showlegend: false
        }];
        
        const layout = {
            title: {
                text: `Corrélation Glissante: ${asset1} vs ${asset2}`,
                font: { size: 16 }
            },
            xaxis: {
                title: 'Date',
                type: 'date'
            },
            yaxis: {
                title: 'Corrélation',
                range: [-1, 1]
            },
            ...this.darkTheme,
            showlegend: true,
            legend: {
                x: 0,
                y: 1,
                bgcolor: 'rgba(30, 41, 59, 0.8)'
            }
        };
        
        const config = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        };
        
        Plotly.newPlot(container, data, layout, config);
    },
    
    // Create statistics table
    createStatisticsTable(statistics, betas) {
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
            
            tableHTML += `
                <tr>
                    <td><strong>${asset}</strong></td>
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
    
    // Display correlation pairs
    displayCorrelationPairs(positivePairs, negativePairs) {
        const positiveContainer = document.getElementById('positive-pairs');
        const negativeContainer = document.getElementById('negative-pairs');
        
        // Display positive correlations
        if (positivePairs.length > 0) {
            positiveContainer.innerHTML = positivePairs.map(pair => `
                <div class="pair-item">
                    <span class="pair-assets">${pair.asset1} - ${pair.asset2}</span>
                    <span class="pair-correlation positive">${pair.correlation.toFixed(3)}</span>
                </div>
            `).join('');
        } else {
            positiveContainer.innerHTML = '<p class="no-data">Aucune paire fortement corrélée positivement</p>';
        }
        
        // Display negative correlations
        if (negativePairs.length > 0) {
            negativeContainer.innerHTML = negativePairs.map(pair => `
                <div class="pair-item">
                    <span class="pair-assets">${pair.asset1} - ${pair.asset2}</span>
                    <span class="pair-correlation negative">${pair.correlation.toFixed(3)}</span>
                </div>
            `).join('');
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
        
        // Period range
        document.getElementById('start-date').textContent = data.start_date;
        document.getElementById('end-date').textContent = data.end_date;
    }
};

// Export for use in other modules
window.ChartModule = ChartModule;