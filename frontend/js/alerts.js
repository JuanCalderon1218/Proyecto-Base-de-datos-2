let selectedAlertId = null;


document.addEventListener(
    "DOMContentLoaded",
    async () => {

        try {

            await loadUser();

            await loadAlerts();

        } catch (error) {

            console.error(
                "Error iniciando alertas:",
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


/* =========================
   CARGAR ALERTAS
========================= */

async function loadAlerts() {

    const tableBody =
        document.getElementById(
            "alertsTableBody"
        );


    tableBody.innerHTML = `
        <tr>
            <td
                colspan="9"
                class="empty-table"
            >
                Cargando alertas...
            </td>
        </tr>
    `;


    const params =
        new URLSearchParams();


    params.append(
        "limit",
        "100"
    );


    const user =
        document.getElementById(
            "filterUser"
        ).value.trim();


    const severity =
        document.getElementById(
            "filterSeverity"
        ).value;


    const status =
        document.getElementById(
            "filterStatus"
        ).value;


    const operation =
        document.getElementById(
            "filterOperation"
        ).value;


    if (user) {

        params.append(
            "user_id",
            user
        );
    }


    if (severity) {

        params.append(
            "severity",
            severity
        );
    }


    if (status) {

        params.append(
            "status",
            status
        );
    }


    if (operation) {

        params.append(
            "operation",
            operation
        );
    }


    try {

        const response =
            await apiFetch(
                `/alerts?${params.toString()}`
            );


        if (!response.ok) {

            throw new Error(
                "No se pudieron cargar las alertas"
            );
        }


        const alerts =
            await response.json();


        renderAlerts(alerts);


    } catch (error) {

        console.error(error);


        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="9"
                    class="empty-table error-text"
                >
                    Error cargando alertas.
                </td>
            </tr>
        `;
    }
}


/* =========================
   RENDER TABLA
========================= */

function renderAlerts(alerts) {

    const tableBody =
        document.getElementById(
            "alertsTableBody"
        );


    document.getElementById(
        "alertCount"
    ).textContent =
        alerts.length;


    if (alerts.length === 0) {

        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="9"
                    class="empty-table"
                >
                    No se encontraron alertas.
                </td>
            </tr>
        `;

        return;
    }


    tableBody.innerHTML = "";


    alerts.forEach(
        alert => {

            const row =
                document.createElement(
                    "tr"
                );


            const types =
                Array.isArray(alert.types)
                    ? alert.types.join(", ")
                    : "-";


            row.innerHTML = `

                <td>
                    ${formatDate(
                        alert.created_at
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        alert.user_id
                    )}
                </td>

                <td>
                    <strong>
                        ${escapeHtml(
                            alert.operation
                        )}
                    </strong>
                </td>

                <td>
                    ${escapeHtml(
                        types
                    )}
                </td>

                <td>
                    <strong>
                        ${alert.score ?? 0}
                    </strong>
                </td>

                <td>
                    ${createSeverityBadge(
                        alert.severity
                    )}
                </td>

                <td>
                    ${createStatusBadge(
                        alert.status
                    )}
                </td>

                <td>
                    ${alert.occurrence_count ?? 1}
                </td>

                <td>
    <button
        class="action-button view-alert-button"
        data-alert-id="${alert.alert_id}"
    >
        Ver detalle
    </button>
</td>
            `;


            tableBody.appendChild(
                row
            );

            const detailButton =
    row.querySelector(
        ".view-alert-button"
    );

detailButton.addEventListener(
    "click",
    () => {

        openAlertDetail(
            detailButton.dataset.alertId
        );
    }
            );
        }
    );
}


/* =========================
   DETALLE ALERTA
========================= */

async function openAlertDetail(
    alertId
) {

    console.log(
        "Abriendo alerta:",
        alertId
    );

    selectedAlertId =
        alertId;


    try {

        const response =
            await apiFetch(
                `/alerts/${alertId}`
            );


        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "Error backend:",
                response.status,
                errorText
            );

            throw new Error(
                "No se pudo cargar la alerta"
            );
        }


        const alertData =
            await response.json();


        console.log(
            "Detalle recibido:",
            alertData
        );


        document.getElementById(
            "modalAlertId"
        ).textContent =
            alertData.alert_id ?? "-";


        document.getElementById(
            "modalUser"
        ).textContent =
            alertData.user_id ?? "-";


        document.getElementById(
            "modalOperation"
        ).textContent =
            alertData.operation ?? "-";


        document.getElementById(
            "modalCollection"
        ).textContent =
            alertData.collection ?? "-";


        document.getElementById(
            "modalRecords"
        ).textContent =
            alertData.records_affected ?? 0;


        document.getElementById(
            "modalScore"
        ).textContent =
            `${alertData.score ?? 0} / 100`;


        document.getElementById(
            "modalSeverity"
        ).innerHTML =
            createSeverityBadge(
                alertData.severity
            );


        renderReasons(
            alertData.reasons
        );


        renderEvidence(
            alertData.detections
        );


        const modal =
            document.getElementById(
                "alertModal"
            );


        modal.classList.add(
            "show"
        );


        console.log(
            "Modal abierto"
        );


    } catch (error) {

        console.error(
            "Error abriendo alerta:",
            error
        );

        window.alert(
            "No se pudo cargar el detalle de la alerta."
        );
    }
}


/* =========================
   MOTIVOS
========================= */

function renderReasons(
    reasons
) {

    const container =
        document.getElementById(
            "modalReasons"
        );


    if (
        !Array.isArray(reasons) ||
        reasons.length === 0
    ) {

        container.innerHTML = `
            <p>
                No hay motivos registrados.
            </p>
        `;

        return;
    }


    container.innerHTML = `
        <ul class="reason-list">

            ${reasons.map(
                reason => `
                    <li>
                        ${escapeHtml(reason)}
                    </li>
                `
            ).join("")}

        </ul>
    `;
}


/* =========================
   EVIDENCIA
========================= */

function renderEvidence(
    detections
) {

    const container =
        document.getElementById(
            "modalEvidence"
        );


    if (
        !Array.isArray(detections) ||
        detections.length === 0
    ) {

        container.innerHTML = `
            <p>
                No hay evidencia disponible.
            </p>
        `;

        return;
    }


    container.innerHTML =
        detections.map(
            detection => {

                const evidence =
                    detection.evidence || {};


                const evidenceRows =
                    Object.entries(
                        evidence
                    )
                    .map(
                        ([key, value]) => `
                            <div
                                class="evidence-row"
                            >
                                <span>
                                    ${formatEvidenceKey(
                                        key
                                    )}
                                </span>

                                <strong>
                                    ${escapeHtml(
                                        value
                                    )}
                                </strong>
                            </div>
                        `
                    )
                    .join("");


                return `

                    <div
                        class="evidence-card"
                    >

                        <div
                            class="evidence-title"
                        >
                            ${escapeHtml(
                                detection.type
                            )}

                            <span>
                                +${detection.score}
                                pts
                            </span>
                        </div>

                        ${evidenceRows}

                    </div>
                `;
            }
        )
        .join("");
}


/* =========================
   CAMBIAR ESTADO
========================= */

async function updateAlertStatus(
    newStatus
) {

    if (!selectedAlertId) {
        return;
    }


    try {

        const response =
            await apiFetch(
                `/alerts/${selectedAlertId}/status`,
                {
                    method: "PATCH",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(
                        {
                            status: newStatus
                        }
                    )
                }
            );


        if (!response.ok) {

            throw new Error(
                "No se pudo actualizar"
            );
        }


        await loadAlerts();


        await openAlertDetail(
            selectedAlertId
        );


    } catch (error) {

        console.error(error);

        alert(
            "No se pudo actualizar el estado."
        );
    }
}


/* =========================
   BADGES
========================= */

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


function createStatusBadge(
    status
) {

    const labels = {
        pending: "Pendiente",
        reviewed: "Revisada",
        resolved: "Resuelta"
    };


    if (!labels[status]) {
        return "-";
    }


    return `
        <span
            class="badge alert-status-${status}"
        >
            ${labels[status]}
        </span>
    `;
}


/* =========================
   UTILIDADES
========================= */

function formatDate(
    timestamp
) {

    if (!timestamp) {
        return "-";
    }


    return new Date(
        timestamp
    ).toLocaleString(
        "es-PE",
        {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        }
    );
}


function formatEvidenceKey(
    key
) {

    return key
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            char => char.toUpperCase()
        );
}


function escapeHtml(
    value
) {

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


/* =========================
   EVENTOS UI
========================= */

document.getElementById(
    "applyFilters"
).addEventListener(
    "click",
    loadAlerts
);


document.getElementById(
    "refreshAlerts"
).addEventListener(
    "click",
    loadAlerts
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
            "filterSeverity"
        ).value = "";

        document.getElementById(
            "filterStatus"
        ).value = "";

        document.getElementById(
            "filterOperation"
        ).value = "";


        await loadAlerts();
    }
);


document.getElementById(
    "closeModal"
).addEventListener(
    "click",
    () => {

        document.getElementById(
            "alertModal"
        ).classList.remove(
            "show"
        );
    }
);


document.querySelectorAll(
    ".status-button"
).forEach(
    button => {

        button.addEventListener(
            "click",
            () => {

                updateAlertStatus(
                    button.dataset.status
                );
            }
        );
    }
);


document.getElementById(
    "alertModal"
).addEventListener(
    "click",
    event => {

        if (
            event.target.id ===
            "alertModal"
        ) {

            event.currentTarget
                .classList.remove(
                    "show"
                );
        }
    }
);