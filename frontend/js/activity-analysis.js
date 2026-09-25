let operationsChart = null;
let hourlyChart = null;
let comparisonChart = null;
let analysisEvents = [];


document.addEventListener(
    "DOMContentLoaded",
    async () => {

        try {

            await loadCurrentUser();

            setToday();

            await loadUsers();

        } catch (error) {

            console.error(
                "Error iniciando análisis:",
                error
            );

        }

    }
);


async function loadCurrentUser() {

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
    
        applyRoleVisibility(
    user
);
}


function setToday() {

    const now =
        new Date();


    const year =
        now.getFullYear();


    const month =
        String(
            now.getMonth() + 1
        ).padStart(
            2,
            "0"
        );


    const day =
        String(
            now.getDate()
        ).padStart(
            2,
            "0"
        );


    document.getElementById(
        "analysisDate"
    ).value =
        `${year}-${month}-${day}`;
}


async function loadUsers() {

    const select =
        document.getElementById(
            "analysisUser"
        );


    select.innerHTML = `
        <option value="">
            Cargando usuarios...
        </option>
    `;


    try {

        const response =
            await apiFetch(
                "/analysis/users"
            );


        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "Error /analysis/users:",
                response.status,
                errorText
            );

            throw new Error(
                "No se pudieron cargar usuarios"
            );
        }


        const data =
            await response.json();


        console.log(
            "Usuarios recibidos:",
            data
        );


        select.innerHTML = `
            <option value="">
                Seleccione usuario
            </option>
        `;


        if (
            !Array.isArray(data.users)
            || data.users.length === 0
        ) {

            select.innerHTML = `
                <option value="">
                    No hay usuarios con eventos
                </option>
            `;

            return;
        }


        data.users.forEach(
            user => {

                const option =
                    document.createElement(
                        "option"
                    );


                option.value =
                    user;

                option.textContent =
                    user;


                select.appendChild(
                    option
                );

            }
        );


    } catch (error) {

        console.error(
            "Error cargando usuarios:",
            error
        );


        select.innerHTML = `
            <option value="">
                Error cargando usuarios
            </option>
        `;
    }


}


async function analyzeActivity() {

    const user =
        document.getElementById(
            "analysisUser"
        ).value;


    const date =
        document.getElementById(
            "analysisDate"
        ).value;


    const historyDays =
        document.getElementById(
            "historyDays"
        ).value;


    if (!user) {

        window.alert(
            "Selecciona un usuario."
        );

        return;

    }


    if (!date) {

        window.alert(
            "Selecciona una fecha."
        );

        return;

    }


    const button =
        document.getElementById(
            "analyzeButton"
        );


    button.disabled = true;

    button.textContent =
        "Analizando...";


    try {

        const response =
            await apiFetch(
                `/analysis/user/${encodeURIComponent(user)}/day`
                + `?date=${encodeURIComponent(date)}`
                + `&history_days=${historyDays}`
            );


        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "Error análisis:",
                response.status,
                errorText
            );

            throw new Error(
                "No se pudo realizar el análisis"
            );
        }


        const data =
            await response.json();


        console.log(
            "Análisis recibido:",
            data
        );


        renderAnalysis(
            data
        );


    } catch (error) {

        console.error(error);

        window.alert(
            "No se pudo realizar el análisis."
        );


    } finally {

        button.disabled = false;

        button.textContent =
            "Analizar";

    }
}


function renderAnalysis(
    data
) {

    document.getElementById(
        "analysisEmpty"
    ).classList.add(
        "hidden"
    );


    document.getElementById(
        "analysisResults"
    ).classList.remove(
        "hidden"
    );


    document.getElementById(
        "analysisTotal"
    ).textContent =
        data.summary.total_events;


    document.getElementById(
        "analysisAnomalies"
    ).textContent =
        data.summary.anomalous_events;


    document.getElementById(
        "analysisSuccess"
    ).textContent =
        data.summary.successful_events;


    document.getElementById(
        "analysisFailures"
    ).textContent =
        data.summary.failed_events;


    document.getElementById(
        "analysisRecords"
    ).textContent =
        data.summary.records_affected;


    renderOperationsChart(
        data.operations,
        data.comparison.operation_averages
    );


    renderHourlyChart(
        data.hourly_activity
    );


    renderComparison(
        data
    );


    renderChanges(
        data.changes
    );


    analysisEvents =
    Array.isArray(data.events)
        ? data.events
        : [];


document.getElementById(
    "analysisHistoryFilter"
).value = "all";


renderEventHistory(
    analysisEvents
);
}


function renderOperationsChart(
    operations,
    averages
) {

    const labels = [
        "READ",
        "INSERT",
        "UPDATE",
        "DELETE"
    ];


    if (operationsChart) {

        operationsChart.destroy();

    }


    operationsChart =
        new Chart(
            document.getElementById(
                "operationsAnalysisChart"
            ),
            {

                type: "bar",

                data: {

                    labels: labels,

                    datasets: [

                        {
                            label:
                                "Día seleccionado",

                            data:
                                labels.map(
                                    operation =>
                                        operations[
                                            operation
                                        ] ?? 0
                                ),

                            backgroundColor:
                                "#2563eb"
                        },

                        {
                            label:
                                "Promedio histórico",

                            data:
                                labels.map(
                                    operation =>
                                        averages[
                                            operation
                                        ] ?? 0
                                ),

                            backgroundColor:
                                "#94a3b8"
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


function renderHourlyChart(
    hourlyActivity
) {

    if (hourlyChart) {

        hourlyChart.destroy();

    }


    hourlyChart =
        new Chart(
            document.getElementById(
                "hourlyAnalysisChart"
            ),
            {

                type: "bar",

                data: {

                    labels:
                        hourlyActivity.map(
                            item => item.hour
                        ),

                    datasets: [
                        {
                            label:
                                "Eventos",

                            data:
                                hourlyActivity.map(
                                    item =>
                                        item.events
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


function renderComparison(
    data
) {

    const current =
        data.summary.total_events;


    const average =
        data.comparison.average_total_events;


    const variation =
        data.comparison.total_variation_percent;


    document.getElementById(
        "comparisonCurrent"
    ).textContent =
        current;


    document.getElementById(
        "comparisonAverage"
    ).textContent =
        average;


    const variationElement =
        document.getElementById(
            "comparisonVariation"
        );


    if (variation === null) {

        variationElement.textContent =
            "Sin base histórica";

    } else {

        variationElement.textContent =
            `${variation > 0 ? "+" : ""}${variation}%`;

    }


    const historical =
        data.comparison.daily_history;


    const labels =
        historical.map(
            item =>
                formatShortDate(
                    item.date
                )
        );


    labels.push(
        "Seleccionado"
    );


    const values =
        historical.map(
            item =>
                item.events
        );


    values.push(
        current
    );


    if (comparisonChart) {

        comparisonChart.destroy();

    }


    comparisonChart =
        new Chart(
            document.getElementById(
                "comparisonChart"
            ),
            {

                type: "line",

                data: {

                    labels: labels,

                    datasets: [
                        {

                            label:
                                "Eventos por día",

                            data: values,

                            borderColor:
                                "#2563eb",

                            backgroundColor:
                                "rgba(37, 99, 235, 0.10)",

                            fill: true,

                            tension: 0.3

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


function renderChanges(
    changes
) {

    const container =
        document.getElementById(
            "analysisChanges"
        );


    if (
        !Array.isArray(changes)
        || changes.length === 0
    ) {

        container.innerHTML = `
            <div class="analysis-ok-message">
                No se detectaron cambios
                importantes respecto al
                comportamiento histórico.
            </div>
        `;

        return;

    }


    container.innerHTML =
        changes.map(
            change => `
                <div class="analysis-change-item">

                    <span class="change-icon">
                        !
                    </span>

                    <p>
                        ${escapeHtml(change)}
                    </p>

                </div>
            `
        ).join("");
}

function filterEventHistory() {

    const filter =
        document.getElementById(
            "analysisHistoryFilter"
        ).value;


    let filteredEvents =
        analysisEvents;


    if (filter === "anomalous") {

        filteredEvents =
            analysisEvents.filter(
                event =>
                    event.is_anomalous === true
            );

    }


    if (filter === "normal") {

        filteredEvents =
            analysisEvents.filter(
                event =>
                    event.is_anomalous !== true
            );

    }


    renderEventHistory(
        filteredEvents
    );
}

function renderEventHistory(
    events
) {

    const body =
        document.getElementById(
            "analysisEventsBody"
        );


    const total =
    analysisEvents.length;


const filtered =
    events.length;


document.getElementById(
    "analysisEventCount"
).textContent =
    filtered === total
        ? `${total} eventos`
        : `${filtered} de ${total} eventos`;


    if (events.length === 0) {

        body.innerHTML = `
            <tr>

                <td
                    colspan="7"
                    class="empty-table"
                >
                    El usuario no tiene eventos
                    registrados en esta fecha.
                </td>

            </tr>
        `;

        return;

    }


    body.innerHTML = "";


    events.forEach(
        event => {

            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td>
                    ${formatTime(
                        event.timestamp
                    )}
                </td>

                <td>
                    <strong>
                        ${escapeHtml(
                            event.operation
                        )}
                    </strong>
                </td>

                <td>
                    ${escapeHtml(
                        event.collection
                    )}
                </td>

                <td>
                    ${event.records_affected ?? 0}
                </td>

                <td>
                    ${
                        event.success
                            ? `
                                <span class="badge badge-success">
                                    Exitoso
                                </span>
                            `
                            : `
                                <span class="badge badge-error">
                                    Fallido
                                </span>
                            `
                    }
                </td>

                <td>
                    ${
                        event.is_anomalous
                            ? `
                                <span class="badge badge-anomaly">
                                    Anómalo
                                </span>
                            `
                            : `
                                <span class="badge badge-normal">
                                    Normal
                                </span>
                            `
                    }
                </td>

                <td>
                    ${createSeverityBadge(
                        event.severity
                    )}
                </td>
            `;


            body.appendChild(
                row
            );

        }
    );
}


function formatTime(
    timestamp
) {

    if (!timestamp) {

        return "-";

    }


    return new Date(
        timestamp
    ).toLocaleTimeString(
        "es-PE",
        {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        }
    );
}


function formatShortDate(
    value
) {

    const parts =
        value.split("-");


    if (parts.length !== 3) {

        return value;

    }


    return `${parts[2]}/${parts[1]}`;
}


function createSeverityBadge(
    severity
) {

    const labels = {

        low: "Baja",

        medium: "Media",

        high: "Alta",

        critical: "Crítica"

    };


    if (!labels[severity]) {

        return "-";

    }


    return `
        <span
            class="badge severity-${severity}"
        >
            ${labels[severity]}
        </span>
    `;
}


function escapeHtml(
    value
) {

    if (
        value === null
        || value === undefined
    ) {

        return "";

    }


    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        String(value);


    return div.innerHTML;
}


document.getElementById(
    "analyzeButton"
).addEventListener(
    "click",
    analyzeActivity
);

document.getElementById(
    "analysisHistoryFilter"
).addEventListener(
    "change",
    filterEventHistory
);