/**
 * dashboard-charts.js
 * Quản lý khởi tạo và tương tác cho 4 biểu đồ Chart.js trên Admin Dashboard
 * 1. Doughnut Chart: Thống kê Ticket theo trạng thái
 * 2. Bar Chart: Thống kê theo mức độ ưu tiên
 * 3. Line Chart: Thống kê sự cố theo thời gian (7 ngày / 30 ngày / Theo tháng)
 * 4. Horizontal Bar Chart: Thống kê theo loại sự cố mạng
 */

let timeSeriesChartInstance = null;
let currentChartData = null;

function initDashboardCharts(data) {
    if (!data || !data.has_data) {
        return;
    }
    currentChartData = data;

    // 1. Biểu đồ trạng thái Ticket (Doughnut Chart)
    const elStatus = document.getElementById('statusChart');
    if (elStatus && data.status) {
        new Chart(elStatus.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: data.status.labels,
                datasets: [{
                    data: data.status.data,
                    backgroundColor: data.status.colors,
                    borderWidth: 2,
                    borderColor: '#ffffff',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, font: { size: 11.5 }, padding: 12 }
                    }
                },
                cutout: '65%'
            }
        });
    }

    // 2. Biểu đồ mức độ ưu tiên (Bar Chart)
    const elPriority = document.getElementById('priorityChart');
    if (elPriority && data.priority) {
        new Chart(elPriority.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.priority.labels,
                datasets: [{
                    label: 'Số lượng sự cố',
                    data: data.priority.data,
                    backgroundColor: data.priority.colors,
                    borderRadius: 6,
                    maxBarThickness: 45,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return ` ${ctx.raw} sự cố`; }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    },
                    x: {
                        ticks: { font: { size: 11 } }
                    }
                }
            }
        });
    }

    // 3. Biểu đồ sự cố theo thời gian (Line Chart)
    const elTime = document.getElementById('timeSeriesChart');
    if (elTime && data.time_series) {
        const initialRange = data.time_series.days_7 || { labels: [], data: [] };
        timeSeriesChartInstance = new Chart(elTime.getContext('2d'), {
            type: 'line',
            data: {
                labels: initialRange.labels,
                datasets: [{
                    label: 'Sự cố phát sinh',
                    data: initialRange.data,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.12)',
                    tension: 0.35,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#2563eb'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return ` ${ctx.raw} ticket`; }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    }

    // 4. Biểu đồ theo loại sự cố mạng (Horizontal Bar Chart)
    const elNetwork = document.getElementById('networkTypeChart');
    if (elNetwork && data.category) {
        new Chart(elNetwork.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.category.labels,
                datasets: [{
                    label: 'Số sự cố',
                    data: data.category.data,
                    backgroundColor: data.category.colors || [
                        '#2563eb', '#06b6d4', '#10b981', '#f59e0b', '#8b5cf6', '#64748b'
                    ],
                    borderRadius: 5,
                    maxBarThickness: 24,
                }]
            },
            options: {
                indexAxis: 'y', // Biểu đồ dạng thanh ngang
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) { return ` ${ctx.raw} sự cố`; }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    },
                    y: {
                        ticks: { font: { size: 11.5 } }
                    }
                }
            }
        });
    }
}

/**
 * Chuyển đổi bộ lọc thời gian: 7 ngày, 30 ngày, theo tháng
 */
function switchTimeRange(rangeKey) {
    if (!timeSeriesChartInstance || !currentChartData || !currentChartData.time_series) {
        return;
    }

    const btn7d = document.getElementById('btn7d');
    const btn30d = document.getElementById('btn30d');
    const btnMonths = document.getElementById('btnMonths');

    if (btn7d) btn7d.classList.remove('active');
    if (btn30d) btn30d.classList.remove('active');
    if (btnMonths) btnMonths.classList.remove('active');

    let targetData = null;
    if (rangeKey === 'days_7') {
        if (btn7d) btn7d.classList.add('active');
        targetData = currentChartData.time_series.days_7;
    } else if (rangeKey === 'days_30') {
        if (btn30d) btn30d.classList.add('active');
        targetData = currentChartData.time_series.days_30;
    } else if (rangeKey === 'months') {
        if (btnMonths) btnMonths.classList.add('active');
        targetData = currentChartData.time_series.months;
    }

    if (targetData) {
        timeSeriesChartInstance.data.labels = targetData.labels;
        timeSeriesChartInstance.data.datasets[0].data = targetData.data;
        timeSeriesChartInstance.update();
    }
}

