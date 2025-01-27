// Configurações globais do Chart.js
Chart.defaults.font.family = "'Segoe UI', 'Helvetica Neue', 'Arial'";
Chart.defaults.font.size = 12;

// Função para carregar os dados do backend
async function loadData() {
    try {
        const response = await fetch('/api/demands');
        const data = await response.json();
        updateDashboard(data);
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
    }
}

// Função para atualizar o dashboard
function updateDashboard(data) {
    updateSummary(data);
    updateCharts(data);
    updateTable(data);
}

// Atualiza o resumo
function updateSummary(data) {
    document.getElementById('totalDemands').textContent = data.total;
    document.getElementById('resolvedDemands').textContent = data.resolved;
    document.getElementById('dailyAverage').textContent = data.dailyAverage.toFixed(1);
    document.getElementById('efficiency').textContent = (data.efficiency * 100).toFixed(1) + '%';
}

// Atualiza os gráficos
function updateCharts(data) {
    updateDailyChart(data.dailyData);
    updateTeamChart(data.teamData);
}

// Gráfico diário
function updateDailyChart(dailyData) {
    const ctx = document.getElementById('dailyChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dailyData.dates,
            datasets: [{
                label: 'Demandas Resolvidas',
                data: dailyData.resolved,
                borderColor: '#007bff',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Demandas Resolvidas por Dia'
                }
            }
        }
    });
}

// Gráfico por equipe
function updateTeamChart(teamData) {
    const ctx = document.getElementById('teamChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: teamData.teams,
            datasets: [{
                label: 'Demandas Resolvidas',
                data: teamData.resolved,
                backgroundColor: '#28a745'
            }, {
                label: 'Demandas Pendentes',
                data: teamData.pending,
                backgroundColor: '#dc3545'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Demandas por Equipe'
                }
            },
            scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true
                }
            }
        }
    });
}

// Atualiza a tabela
function updateTable(data) {
    const tbody = document.getElementById('teamDetails');
    tbody.innerHTML = '';
    
    data.teamDetails.forEach(team => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${team.name}</td>
            <td>${team.total}</td>
            <td>${team.resolved}</td>
            <td>${team.pending}</td>
            <td>${(team.efficiency * 100).toFixed(1)}%</td>
            <td>${team.dailyAverage.toFixed(1)}</td>
            <td>${team.weeklyAverage.toFixed(1)}</td>
        `;
        tbody.appendChild(row);
    });
}

// Event listeners para filtros
document.getElementById('dateRange').addEventListener('change', loadData);
document.getElementById('team').addEventListener('change', loadData);
document.getElementById('status').addEventListener('change', loadData);

// Carrega dados iniciais
loadData();
