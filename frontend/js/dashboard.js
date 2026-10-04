let severityChart;
let operationChart;
let dailyChart;
let userChart;


document.addEventListener(
    "DOMContentLoaded",
    async () => {

        try {

            await loadUser();

            await Promise.all([
                loadSummary(),
                loadSeverityChart(),
                loadOperationChart(),
                loadDailyChart(),
                loadUserChart()
            ]);

        } catch (error) {

            console.error(
                "Error cargando dashboard:",
                error
            );
        }
    }
);


async function loadUser() {

    const user =
        await getCurrentUser();


    console.log(
        "Usuario autenticado:",
        user
    );


    document.getElementById(
        "currentUsername"
    ).textContent =
        user.username;


    document.getElementById(
        "currentRole"
    ).textContent =
        user.role;


    applyRoleVisibility(
        user
    );
}


/* ========================
   RESUMEN
======================== */

async function loadSummary() {

    const response =
        await apiFetch(
            "/dashboard/summary"
        );

    if (!response.ok) {
        throw new Error(
            "Error cargando resumen"
        );
    }

    const data =
        await response.json();

    document.getElementById(
        "totalEvents"
    ).textContent =
        data.events.total;

    document.getElementById(
        "totalAlerts"
    ).textContent =
        data.alerts.total;

    document.getElementById(
        "criticalAlerts"
    ).textContent =
        data.alerts.critical;

    document.getElementById(
        "pendingAlerts"
    ).textContent =
        data.alerts.pending;
}


/* ========================
   SEVERIDAD
======================== */

async function loadSeverityChart() {

    const response =
        await apiFetch(
            "/statistics/alerts-by-severity"
        );

    const data =
        await response.json();

    const labels =
        data.map(
            item => item.severity
        );

    const values =
        data.map(
            item => item.count
        );

    severityChart =
        new Chart(
            document.getElementById(
                "severityChart"
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
                            ]
                        }
                    ]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            }
        );
}


/* ========================
   OPERACIONES
======================== */

async function loadOperationChart() {

    const response =
        await apiFetch(
            "/statistics/events-by-operation"
        );

    const data =
        await response.json();

    operationChart =
        new Chart(
            document.getElementById(
                "operationChart"
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
                                "#2563eb"
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
                            beginAtZero: true
                        }
                    }
                }
            }
        );
}


/* ========================
   ACTIVIDAD DIARIA
======================== */

async function loadDailyChart() {

    const response =
        await apiFetch(
            "/statistics/daily-activity?days=7"
        );

    const data =
        await response.json();

    dailyChart =
        new Chart(
            document.getElementById(
                "dailyChart"
            ),
            {
                type: "line",

                data: {
                    labels:
                        data.map(
                            item =>
                                item.date
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

                            borderColor:
                                "#2563eb",

                            backgroundColor:
                                "#2563eb",

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
                                "#dc2626",

                            tension: 0.3
                        }
                    ]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        );
}


/* ========================
   USUARIOS
======================== */

async function loadUserChart() {

    const response =
        await apiFetch(
            "/statistics/activity-by-user?limit=5"
        );

    const data =
        await response.json();

    userChart =
        new Chart(
            document.getElementById(
                "userChart"
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
                                "#2563eb"
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
                                "#dc2626"
                        }
                    ]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        );
}