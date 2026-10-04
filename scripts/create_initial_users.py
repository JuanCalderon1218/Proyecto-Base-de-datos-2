import asyncio
from datetime import datetime, timezone
from getpass import getpass

from backend.app.auth.security import (
    hash_password,
)
from backend.app.database.connection import (
    client,
    database,
)


async def create_user(
    username: str,
    role: str,
):
    existing = await database[
        "users"
    ].find_one(
        {
            "username": username
        }
    )

    if existing:
        print(
            f"El usuario '{username}' "
            "ya existe."
        )
        return

    password = getpass(
        f"Contraseña para {username}: "
    )

    if len(password) < 8:
        print(
            "La contraseña debe tener "
            "al menos 8 caracteres."
        )
        return

    confirmation = getpass(
        "Repite la contraseña: "
    )

    if password != confirmation:
        print(
            "Las contraseñas no coinciden."
        )
        return

    user = {
        "username": username,
        "password_hash":
            hash_password(password),
        "role": role,
        "active": True,
        "created_at":
            datetime.now(timezone.utc),
    }

    await database["users"].insert_one(
        user
    )

    print(
        f"Usuario '{username}' "
        f"creado como {role}."
    )


async def main():

    await create_user(
        "admin",
        "admin",
    )

    await create_user(
        "analyst",
        "analyst",
    )

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())