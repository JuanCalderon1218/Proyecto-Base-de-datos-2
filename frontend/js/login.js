const loginForm = document.getElementById(
    "loginForm"
);

const loginError = document.getElementById(
    "loginError"
);


loginForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();

        loginError.textContent = "";

        const username =
            document.getElementById(
                "username"
            ).value.trim();

        const password =
            document.getElementById(
                "password"
            ).value;

        const body =
            new URLSearchParams();

        body.append(
            "username",
            username
        );

        body.append(
            "password",
            password
        );

        try {

            const response = await fetch(
                "/auth/login",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/x-www-form-urlencoded"
                    },

                    body: body
                }
            );

            if (!response.ok) {

                loginError.textContent =
                    "Usuario o contraseña incorrectos.";

                return;
            }

            const data =
                await response.json();

            saveToken(
                data.access_token
            );

            window.location.href =
                "/dashboard";

        } catch (error) {

            console.error(error);

            loginError.textContent =
                "No se pudo conectar con el servidor.";
        }
    }
);