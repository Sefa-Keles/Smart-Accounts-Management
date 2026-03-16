document.addEventListener('DOMContentLoaded', function () {
    const labelsElement = document.getElementById('expense-category-labels');
    const totalsElement = document.getElementById('expense-category-totals');
    const chartCanvas = document.getElementById('expenseCategoryChart');

    if (!labelsElement || !totalsElement || !chartCanvas || typeof Chart === 'undefined') {
        return;
    }

    const labels = JSON.parse(labelsElement.textContent);
    const totals = JSON.parse(totalsElement.textContent);

    new Chart(chartCanvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [
                {
                    data: totals,
                    radius: '82%',
                    cutout: '58%',
                    backgroundColor: [
                        '#1f3a5f',
                        '#2f5f93',
                        '#4b7cb0',
                        '#6b97c2',
                        '#90b2d3',
                        '#b8cde2',
                        '#dbe7f3'
                    ],
                    borderWidth: 1,
                }
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                },
            },
        },
    });
});
