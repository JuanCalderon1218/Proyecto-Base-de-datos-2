document.addEventListener(
    "DOMContentLoaded",
    async () => {

        try {

            await loadUser();

            await loadEvents();

        } catch (error) {

            console.error(
                "Error iniciando eventos:",
                error
            );
        }
    }
);


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

    applyRoleVisibility(
    user
);
}


async function loadEvents() {

    const tableBody =
        document.getElementById(
            "eventsTableBody"
        );

    tableBody.innerHTML = `
        <tr>
            <td
                colspan="8"
                class="empty-table"
            >
                Cargando eventos...
            </td>
        </tr>
    `;


    const userId =
        document.getElementById(
            "filterUser"
        ).value.trim();

    const operation =
        document.getElementById(
            "filterOperation"
        ).value;

    const anomalous =
        document.getElementById(
            "filterAnomalous"
        ).value;

    const success =
        document.getElementById(
            "filterSuccess"
        ).value;


    const params =
        new URLSearchParams();

    params.append(
        "limit",
        "100"
    );


    if (userId) {

        params.append(
            "user_id",
            userId
        );
    }


    if (operation) {

        params.append(
            "operation",
            operation
        );
    }


    if (anomalous !== "") {

        params.append(
            "anomalous",
            anomalous
        );
    }


    if (success !== "") {

        params.append(
            "success",
            success
        );
    }


    try {

        const response =
            await apiFetch(
                `/events?${params.toString()}`
            );


        if (!response.ok) {

            throw new Error(
                "No se pudieron cargar los eventos"
            );
        }


        const events =
            await response.json();


        renderEvents(events);


    } catch (error) {

        console.error(error);

        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="8"
                    class="empty-table error-text"
                >
                    Error cargando eventos.
                </td>
            </tr>
        `;
    }
}


function renderEvents(events) {

    const tableBody =
        document.getElementById(
            "eventsTableBody"
        );


    document.getElementById(
        "eventCount"
    ).textContent =
        events.length;


    if (events.length === 0) {

        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="8"
                    class="empty-table"
                >
                    No se encontraron eventos.
                </td>
            </tr>
        `;

        return;
    }


    tableBody.innerHTML = "";


    events.forEach(
        event => {

            const row =
                document.createElement(
                    "tr"
                );


            const date =
                formatDate(
                    event.timestamp
                );


            const statusBadge =
                event.success
                    ? `
                        <span
                            class="badge badge-success"
                        >
                            Exitoso
                        </span>
                    `
                    : `
                        <span
                            class="badge badge-error"
                        >
                            Fallido
                        </span>
                    `;


            const anomalyBadge =
                event.is_anomalous
                    ? `
                        <span
                            class="badge badge-anomaly"
                        >
                            Anómalo
                        </span>
                    `
                    : `
                        <span
                            class="badge badge-normal"
                        >
                            Normal
                        </span>
                    `;


            const severity =
                createSeverityBadge(
                    event.severity
                );


            row.innerHTML = `
                <td>${date}</td>

                <td>
                    ${escapeHtml(
                        event.user_id
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
                    ${event.records_affected}
                </td>

                <td>
                    ${statusBadge}
                </td>

                <td>
                    ${anomalyBadge}
                </td>

                <td>
                    ${severity}
                </td>
            `;


            tableBody.appendChild(
                row
            );
        }
    );
}


function createSeverityBadge(
    severity
) {

    if (!severity) {

        return `
            <span
                class="badge badge-none"
            >
                -
            </span>
        `;
    }


    const allowed = [
        "low",
        "medium",
        "high",
        "critical"
    ];


    if (!allowed.includes(severity)) {

        return "-";
    }


    const labels = {
        low: "Baja",
        medium: "Media",
        high: "Alta",
        critical: "Crítica"
    };


    return `
        <span
            class="badge severity-${severity}"
        >
            ${labels[severity]}
        </span>
    `;
}


function formatDate(
    timestamp
) {

    if (!timestamp) {
        return "-";
    }


    const date =
        new Date(timestamp);


    return date.toLocaleString(
        "es-PE",
        {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        }
    );
}


function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
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
    "applyFilters"
).addEventListener(
    "click",
    loadEvents
);


document.getElementById(
    "clearFilters"
).addEventListener(
    "click",
    async () => {

        document.getElementById(
            "filterUser"
        ).value = "";

        document.getElementById(
            "filterOperation"
        ).value = "";

        document.getElementById(
            "filterAnomalous"
        ).value = "";

        document.getElementById(
            "filterSuccess"
        ).value = "";

        await loadEvents();
    }
);


document.getElementById(
    "refreshEvents"
).addEventListener(
    "click",
    loadEvents
);