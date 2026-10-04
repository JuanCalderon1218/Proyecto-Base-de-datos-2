const TOKEN_KEY = "access_token";


function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}


function saveToken(token) {
    localStorage.setItem(
        TOKEN_KEY,
        token
    );
}


function removeToken() {
    localStorage.removeItem(TOKEN_KEY);
}


function logout() {
    removeToken();

    window.location.href = "/";
}


async function apiFetch(
    url,
    options = {}
) {
    const token = getToken();

    const headers = new Headers(
        options.headers || {}
    );

    headers.set(
        "Accept",
        "application/json"
    );

    if (token) {
        headers.set(
            "Authorization",
            `Bearer ${token}`
        );
    }

    const response = await fetch(
        url,
        {
            ...options,
            headers
        }
    );

    if (response.status === 401) {
        removeToken();

        window.location.href = "/";

        throw new Error(
            "Sesión expirada"
        );
    }

    return response;
}


async function getCurrentUser() {

    const response = await apiFetch(
        "/auth/me"
    );

    if (!response.ok) {
        throw new Error(
            "No se pudo obtener el usuario"
        );
    }

    return await response.json();
}

function applyRoleVisibility(user) {

    console.log(
        "Rol actual:",
        user.role
    );


    document.querySelectorAll(
        ".admin-nav-item"
    ).forEach(
        element => {

            if (user.role === "admin") {

                element.style.display =
                    "block";

            } else {

                element.style.display =
                    "none";

            }

        }
    );
}