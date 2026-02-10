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
                    '#29b6d8', // Teal
                    'rgba(87, 199, 112, 0.4)' // Green with opacity
                ],
                borderColor: [
                    '#29b6d8',
                    '#57c770'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#8a9ba8',
                        font: { family: "'Space Grotesk', sans-serif" }
                    }
                }
            },
            cutout: '70%'
        }
    });
});
