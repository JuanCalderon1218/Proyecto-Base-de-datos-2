let selectedPasswordUser = null;


document.addEventListener(
    "DOMContentLoaded",
    async () => {

        try {

            const user =
                await getCurrentUser();


            if (
                user.role !== "admin"
            ) {

                window.location.href =
                    "/dashboard";

                return;
            }


            document.getElementById(
                "currentUsername"
            ).textContent =
                user.username;


            document.getElementById(
                "currentRole"
            ).textContent =
                user.role;


            await loadUsers();


        } catch (error) {

            console.error(
                "Error iniciando usuarios:",
                error
            );

        }

    }
);


async function loadUsers() {

    const body =
        document.getElementById(
            "usersTableBody"
        );


    body.innerHTML = `
        <tr>
            <td
                colspan="6"
                class="empty-table"
            >
                Cargando usuarios...
            </td>
        </tr>
    `;


    try {

        const response =
            await apiFetch(
                "/users"
            );


        if (response.status === 403) {

            window.location.href =
                "/dashboard";

            return;
        }


        if (!response.ok) {

            throw new Error(
                "No se pudieron cargar usuarios"
            );
        }


        const users =
            await response.json();


        renderUsers(
            users
        );


    } catch (error) {

        console.error(error);


        body.innerHTML = `
            <tr>
                <td
                    colspan="6"
                    class="empty-table error-text"
                >
                    Error cargando usuarios.
                </td>
            </tr>
        `;

    }
}


function renderUsers(
    users
) {

    const body =
        document.getElementById(
            "usersTableBody"
        );


    body.innerHTML = "";


    users.forEach(
        user => {

            const row =
                document.createElement(
                    "tr"
                );


            const isAdmin =
                user.role === "admin";


            const statusBadge =
                user.active
                    ? `
                        <span
                            class="badge badge-success"
                        >
                            Activo
                        </span>
                    `
                    : `
                        <span
                            class="badge badge-error"
                        >
                            Inactivo
                        </span>
                    `;


            let actions = `
                <span class="admin-protected-label">
                    Administrador principal
                </span>
            `;


            if (!isAdmin) {

                const activeText =
                    user.active
                        ? "Desactivar"
                        : "Activar";


                actions = `

                    <button
                        class="action-button"
                        data-action="password"
                        data-username="${escapeHtml(
                            user.username
                        )}"
                    >
                        Contraseña
                    </button>


                    <button
                        class="
                            user-status-button
                            ${
                                user.active
                                    ? "deactivate-button"
                                    : "activate-button"
                            }
                        "
                        data-action="active"
                        data-username="${escapeHtml(
                            user.username
                        )}"
                        data-active="${user.active}"
                    >
                        ${activeText}
                    </button>
                `;

            }


            row.innerHTML = `

                <td>
                    <strong>
                        ${escapeHtml(
                            user.username
                        )}
                    </strong>
                </td>

                <td>
                    ${formatRole(
                        user.role
                    )}
                </td>

                <td>
                    ${statusBadge}
                </td>

                <td>
                    ${formatDate(
                        user.created_at
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        user.created_by
                        ?? "-"
                    )}
                </td>

                <td class="user-actions">
                    ${actions}
                </td>
            `;


            body.appendChild(
                row
            );

        }
    );


    bindUserButtons();
}


function bindUserButtons() {

    document.querySelectorAll(
        '[data-action="active"]'
    ).forEach(
        button => {

            button.addEventListener(
                "click",
                async () => {

                    const username =
                        button.dataset.username;


                    const currentActive =
                        button.dataset.active
                        === "true";


                    await changeUserStatus(
                        username,
                        !currentActive
                    );

                }
            );

        }
    );


    document.querySelectorAll(
        '[data-action="password"]'
    ).forEach(
        button => {

            button.addEventListener(
                "click",
                () => {

                    openPasswordModal(
                        button.dataset.username
                    );

                }
            );

        }
    );
}


async function changeUserStatus(
    username,
    active
) {

    const action =
        active
            ? "activar"
            : "desactivar";


    const confirmed =
        window.confirm(
            `¿Deseas ${action} al usuario ${username}?`
        );


    if (!confirmed) {

        return;

    }


    try {

        const response =
            await apiFetch(
                `/users/${encodeURIComponent(username)}/active`,
                {

                    method:
                        "PATCH",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            {
                                active: active
                            }
                        )

                }
            );


        if (!response.ok) {

            const data =
                await response.json();


            throw new Error(
                data.detail
                ?? "No se pudo actualizar"
            );

        }


        await loadUsers();


    } catch (error) {

        console.error(error);

        window.alert(
            error.message
        );

    }
}


function openPasswordModal(
    username
) {

    selectedPasswordUser =
        username;


    document.getElementById(
        "passwordUsername"
    ).textContent =
        username;


    document.getElementById(
        "resetPassword"
    ).value = "";


    document.getElementById(
        "passwordError"
    ).textContent = "";


    document.getElementById(
        "passwordModal"
    ).classList.add(
        "show"
    );
}


document.getElementById(
    "openCreateUser"
).addEventListener(
    "click",
    () => {

        document.getElementById(
            "createUserForm"
        ).reset();


        document.getElementById(
            "createUserError"
        ).textContent = "";


        document.getElementById(
            "createUserModal"
        ).classList.add(
            "show"
        );

    }
);


document.getElementById(
    "closeCreateUser"
).addEventListener(
    "click",
    () => {

        document.getElementById(
            "createUserModal"
        ).classList.remove(
            "show"
        );

    }
);


document.getElementById(
    "closePasswordModal"
).addEventListener(
    "click",
    () => {

        document.getElementById(
            "passwordModal"
        ).classList.remove(
            "show"
        );

    }
);


document.getElementById(
    "createUserForm"
).addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        const username =
            document.getElementById(
                "newUsername"
            ).value.trim();


        const password =
            document.getElementById(
                "newPassword"
            ).value;


        const confirmation =
            document.getElementById(
                "confirmPassword"
            ).value;


        const error =
            document.getElementById(
                "createUserError"
            );


        error.textContent = "";


        if (
            password !== confirmation
        ) {

            error.textContent =
                "Las contraseñas no coinciden.";

            return;
        }


        try {

            const response =
                await apiFetch(
                    "/users",
                    {

                        method:
                            "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                {
                                    username:
                                        username,

                                    password:
                                        password,

                                    role:
                                        "analyst"
                                }
                            )

                    }
                );


            if (!response.ok) {

                const data =
                    await response.json();


                error.textContent =
                    data.detail
                    ?? "No se pudo crear el usuario";

                return;

            }


            document.getElementById(
                "createUserModal"
            ).classList.remove(
                "show"
            );


            await loadUsers();


        } catch (requestError) {

            console.error(
                requestError
            );


            error.textContent =
                "Error de conexión.";

        }

    }
);


document.getElementById(
    "passwordForm"
).addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        if (!selectedPasswordUser) {

            return;

        }


        const password =
            document.getElementById(
                "resetPassword"
            ).value;


        const error =
            document.getElementById(
                "passwordError"
            );


        error.textContent = "";


        try {

            const response =
                await apiFetch(
                    `/users/${encodeURIComponent(
                        selectedPasswordUser
                    )}/password`,
                    {

                        method:
                            "PATCH",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                {
                                    password:
                                        password
                                }
                            )

                    }
                );


            if (!response.ok) {

                const data =
                    await response.json();


                error.textContent =
                    data.detail
                    ?? "No se pudo cambiar la contraseña";

                return;

            }


            document.getElementById(
                "passwordModal"
            ).classList.remove(
                "show"
            );


            window.alert(
                "Contraseña actualizada correctamente."
            );


        } catch (requestError) {

            console.error(
                requestError
            );


            error.textContent =
                "Error de conexión.";

        }

    }
);


function formatRole(
    role
) {

    return role === "admin"
        ? "Administrador"
        : "Analista";
}


function formatDate(
    value
) {

    if (!value) {

        return "-";

    }


    return new Date(
        value
    ).toLocaleString(
        "es-PE",
        {
            year:
                "numeric",

            month:
                "2-digit",

            day:
                "2-digit",

            hour:
                "2-digit",

            minute:
                "2-digit"
        }
    );
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