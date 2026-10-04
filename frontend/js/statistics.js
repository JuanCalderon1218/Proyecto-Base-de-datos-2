let severityStatsChart = null;
let operationsStatsChart = null;
let dailyStatsChart = null;
let usersStatsChart = null;


document.addEventListener(
    "DOMContentLoaded",
    async () => {

        try {

            await loadUser();

            await loadAllStatistics();

        } catch (error) {

            console.error(
                "Error cargando estadísticas:",
                error
            );

        }

    }
);


/* =========================
   USUARIO
========================= */

async function loadUser() {

    const user =
        await getCurrentUser();


    document.getElementById(
        "currentUsername"
    ).textContent =
        user.username;


    document.getElementById(
        "currentRole"
    ).textContent =
        user.role;
}


/* =========================
   CARGAR TODO
========================= */

async function loadAllStatistics() {

    const days =
        document.getElementById(
            "daysFilter"
        ).value;


    await Promise.all([
        loadSummary(),
        loadSeverityStatistics(),
        loadOperationStatistics(),
        loadDailyStatistics(days),
        loadUserStatistics()
    ]);

}


/* =========================
   RESUMEN
========================= */

async function loadSummary() {

    const response =
        await apiFetch(
            "/dashboard/summary"
        );


    if (!response.ok) {

        throw new Error(
            "No se pudo cargar el resumen"
        );

    }


    const data =
        await response.json();


    const totalEvents =
        data.events.total ?? 0;


    const anomalousEvents =
        data.events.anomalous ?? 0;


    const anomalyRate =
        totalEvents > 0
            ? (
                (
                    anomalousEvents /
                    totalEvents
                ) * 100
            ).toFixed(1)
            : 0;


    document.getElementById(
        "statsTotalEvents"
    ).textContent =
        totalEvents;


    document.getElementById(
        "statsAnomalousEvents"
    ).textContent =
        anomalousEvents;


    document.getElementById(
        "statsAnomalyRate"
    ).textContent =
        `${anomalyRate}%`;


    document.getElementById(
        "statsCriticalAlerts"
    ).textContent =
        data.alerts.critical ?? 0;


    document.getElementById(
        "statsPending"
    ).textContent =
        data.alerts.pending ?? 0;


    document.getElementById(
        "statsReviewed"
    ).textContent =
        data.alerts.reviewed ?? 0;


    document.getElementById(
        "statsResolved"
    ).textContent =
        data.alerts.resolved ?? 0;


    document.getElementById(
        "statsTotalAlerts"
    ).textContent =
        data.alerts.total ?? 0;
}


/* =========================
   SEVERIDAD
========================= */

async function loadSeverityStatistics() {

    const response =
        await apiFetch(
            "/statistics/alerts-by-severity"
        );


    if (!response.ok) {

        throw new Error(
            "Error cargando severidades"
        );

    }


    const data =
        await response.json();


    const labels = data.map(
        item => {

            const names = {
                low: "Baja",
                medium: "Media",
                high: "Alta",
                critical: "Crítica"
            };

            return (
                names[item.severity]
                ?? item.severity
            );

        }
    );


    const values =
        data.map(
            item => item.count
        );


    if (severityStatsChart) {

        severityStatsChart.destroy();

    }


    severityStatsChart =
        new Chart(
            document.getElementById(
                "severityStatsChart"
            ),
            {

                type: "doughnut",

                data: {

                    labels: labels,

                    datasets: [
                        {

                            data: values,

                            backgroundColor: [
                                "#22c55e",
                                "#eab308",
                                "#f97316",
                                "#dc2626"
                            ],

                            borderWidth: 0

                        }
                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {

                            position: "bottom"

                        }

                    }

                }

            }
        );
}


/* =========================
   OPERACIONES
========================= */

async function loadOperationStatistics() {

    const response =
        await apiFetch(
            "/statistics/events-by-operation"
        );


    if (!response.ok) {

        throw new Error(
            "Error cargando operaciones"
        );

    }


    const data =
        await response.json();


    if (operationsStatsChart) {

        operationsStatsChart.destroy();

    }


    operationsStatsChart =
        new Chart(
            document.getElementById(
                "operationsStatsChart"
            ),
            {

                type: "bar",

                data: {

                    labels:
                        data.map(
                            item =>
                                item.operation
                        ),

                    datasets: [
                        {

                            label:
                                "Eventos",

                            data:
                                data.map(
                                    item =>
                                        item.count
                                ),

                            backgroundColor:
                                "#2563eb",

                            borderRadius: 6

                        }
                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {

                            display: false

                        }

                    },

                    scales: {

                        y: {

                            beginAtZero: true,

                            ticks: {

                                precision: 0

                            }

                        }

                    }

                }

            }
        );
}


/* =========================
   ACTIVIDAD DIARIA
========================= */

async function loadDailyStatistics(
    days
) {

    const response =
        await apiFetch(
            `/statistics/daily-activity?days=${days}`
        );


    if (!response.ok) {

        throw new Error(
            "Error cargando actividad diaria"
        );

    }


    const data =
        await response.json();


    const labels =
        data.map(
            item =>
                formatChartDate(
                    item.date
                )
        );


    if (dailyStatsChart) {

        dailyStatsChart.destroy();

    }


    dailyStatsChart =
        new Chart(
            document.getElementById(
                "dailyStatsChart"
            ),
            {

                type: "line",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            label:
                                "Eventos",

                            data:
                                data.map(
                                    item =>
                                        item.events
                                ),

                            borderColor:
                                "#2563eb",

                            backgroundColor:
                                "rgba(37, 99, 235, 0.12)",

                            fill: true,

                            tension: 0.3

                        },


                        {

                            label:
                                "Anomalías",

                            data:
                                data.map(
                                    item =>
                                        item.anomalies
                                ),

                            borderColor:
                                "#dc2626",

                            backgroundColor:
                                "rgba(220, 38, 38, 0.08)",

                            fill: true,

                            tension: 0.3

                        }

                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {

                        mode: "index",

                        intersect: false

                    },

                    scales: {

                        y: {

                            beginAtZero: true,

                            ticks: {

                                precision: 0

                            }

                        }

                    }

                }

            }
        );
}


/* =========================
   USUARIOS
========================= */

async function loadUserStatistics() {

    const response =
        await apiFetch(
            "/statistics/activity-by-user?limit=10"
        );


    if (!response.ok) {

        throw new Error(
            "Error cargando usuarios"
        );

    }


    const data =
        await response.json();


    if (usersStatsChart) {

        usersStatsChart.destroy();

    }


    usersStatsChart =
        new Chart(
            document.getElementById(
                "usersStatsChart"
            ),
            {

                type: "bar",

                data: {

                    labels:
                        data.map(
                            item =>
                                item.user_id
                        ),

                    datasets: [

                        {

                            label:
                                "Eventos",

                            data:
                                data.map(
                                    item =>
                                        item.events
                                ),

                            backgroundColor:
                                "#2563eb",

                            borderRadius: 5

                        },


                        {

                            label:
                                "Anomalías",

                            data:
                                data.map(
                                    item =>
                                        item.anomalies
                                ),

                            backgroundColor:
                                "#dc2626",

                            borderRadius: 5

                        }

                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    scales: {

                        y: {

                            beginAtZero: true,

                            ticks: {

                                precision: 0

                            }

                        }

                    }

                }

            }
        );
}


/* =========================
   FECHAS
========================= */

function formatChartDate(
    dateString
) {

    if (!dateString) {

        return "-";

    }


    const parts =
        dateString.split("-");


    if (parts.length !== 3) {

        return dateString;

    }


    return (
        `${parts[2]}/${parts[1]}`
    );
}


/* =========================
   EVENTOS UI
========================= */

document.getElementById(
    "daysFilter"
).addEventListener(
    "change",
    async event => {

        await loadDailyStatistics(
            event.target.value
        );

    }
);


document.getElementById(
    "refreshStatistics"
).addEventListener(
    "click",
    loadAllStatistics
);