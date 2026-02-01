document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('activityChart');
    if (!ctx) return;

    // Use data passed from template via global variable or data attributes
    // Assuming simple comparison for now

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Visits', 'Credentials Captured'],
            datasets: [{
                label: 'Campaign Performance',
                data: [chartData.visits, chartData.creds],
                backgroundColor: [
                    '#6366f1',
                    '#ef4444'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8' }
                }
            }
        }
    });
});
