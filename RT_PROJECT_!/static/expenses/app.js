document.addEventListener('DOMContentLoaded', () => {
    // 1. Reveal Animations & Pulse
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const revealItems = document.querySelectorAll('.reveal-item');

    if (prefersReducedMotion) {
        revealItems.forEach((item) => item.classList.add('visible'));
    } else {
        requestAnimationFrame(() => {
            revealItems.forEach((item, index) => {
                setTimeout(() => {
                    item.classList.add('visible');
                }, 60 * index);
            });
        });

        const totalCards = document.querySelectorAll('[data-total-card]');
        totalCards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('pulse');
                card.addEventListener(
                    'animationend',
                    () => {
                        card.classList.remove('pulse');
                    },
                    { once: true }
                );
            }, 120 + index * 45);
        });
    }

    // 2. Chart.js Initialization
    const chartDataElement = document.getElementById('chart-data');
    if (chartDataElement) {
        try {
            const categoryTotals = JSON.parse(chartDataElement.textContent);

            // Map values, defaulting to 0 if undefined
            const foodVal = parseFloat(categoryTotals.food) || 0;
            const rentVal = parseFloat(categoryTotals.rent) || 0;
            const funVal = parseFloat(categoryTotals.fun) || 0;

            const ctx = document.getElementById('expenseChart').getContext('2d');

            // If everything is 0, show a placeholder
            const total = foodVal + rentVal + funVal;
            const dataValues = total > 0 ? [foodVal, rentVal, funVal] : [1];
            const dataColors = total > 0
                ? ['#f59e0b', '#ec4899', '#06b6d4'] // Amber, Pink, Cyan
                : ['rgba(148, 163, 184, 0.2)']; // Empty state Slate

            const dataLabels = total > 0 ? ['Food', 'Rent', 'Fun'] : ['No Data'];

            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: dataLabels,
                    datasets: [{
                        data: dataValues,
                        backgroundColor: dataColors,
                        borderWidth: 0,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '75%', // Modern thin donut
                    plugins: {
                        legend: {
                            display: false // We have custom legend cards below
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleFont: { family: 'Inter', size: 14 },
                            bodyFont: { family: 'Inter', size: 14 },
                            padding: 12,
                            cornerRadius: 8,
                            callbacks: {
                                label: function (context) {
                                    if (total === 0) return ' Log an expense to see data';
                                    let label = context.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed !== null) {
                                        label += new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(context.parsed);
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    animation: {
                        animateScale: true,
                        animateRotate: true,
                        duration: 2000,
                        easing: 'easeOutQuart'
                    }
                }
            });
        } catch (e) {
            console.error("Failed to parse chart data", e);
        }
    }
});
