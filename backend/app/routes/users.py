from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from backend.app.auth.security import (
    hash_password,
    require_roles,
)

from backend.app.database.connection import (
    database,
)

from backend.app.schemas.user import (
    UserActiveUpdate,
    UserCreate,
    UserPasswordReset,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# ==========================================
# LISTAR USUARIOS
# ==========================================

@router.get("")
async def get_users(
    current_user=Depends(
        require_roles("admin")
    ),
):

    users = []

    cursor = (
        database["users"]
        .find(
            {},
            {
                "_id": 0,
                "password_hash": 0,
            },
        )
        .sort(
            "username",
            1,
        )
    )


    async for user in cursor:

        users.append(
            user
        )


    return users


# ==========================================
# CREAR ANALISTA
# ==========================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate,

    current_user=Depends(
        require_roles("admin")
    ),
):

    username = (
        user_data.username
        .strip()
        .lower()
    )


    existing_user = await database[
        "users"
    ].find_one(
        {
            "username": username
        }
    )


    if existing_user:

        raise HTTPException(
            status_code=409,
            detail=(
                "Ya existe un usuario "
                "con ese nombre"
            ),
        )


    document = {

        "username":
            username,

        "password_hash":
            hash_password(
                user_data.password
            ),

        "role":
            "analyst",

        "active":
            True,

        "created_at":
            datetime.now(
                timezone.utc
            ),

        "created_by":
            current_user[
                "username"
            ],
    }


    await database[
        "users"
    ].insert_one(
        document
    )


    return {
        "message":
            "Usuario creado correctamente",

        "username":
            username,

        "role":
            "analyst",

        "active":
            True,
    }


# ==========================================
# ACTIVAR / DESACTIVAR
# ==========================================

@router.patch(
    "/{username}/active"
)
async def update_user_active(
    username: str,

    update: UserActiveUpdate,

    current_user=Depends(
        require_roles("admin")
    ),
):

    user = await database[
        "users"
    ].find_one(
        {
            "username": username
        }
    )


    if user is None:

        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )


    # El administrador principal
    # no puede desactivarse.

    if (
        user.get("role") == "admin"
        and update.active is False
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "El administrador principal "
                "no puede ser desactivado"
            ),
        )


    await database[
        "users"
    ].update_one(
        {
            "username": username
        },
        {
            "$set": {

                "active":
                    update.active,

                "updated_at":
                    datetime.now(
                        timezone.utc
                    ),

                "updated_by":
                    current_user[
                        "username"
                    ],
            }
        },
    )


    return {
        "message":
            "Estado actualizado correctamente",

        "username":
            username,

        "active":
            update.active,
    }


# ==========================================
# RESTABLECER CONTRASEÑA
# ==========================================

@router.patch(
    "/{username}/password"
)
async def reset_user_password(
    username: str,

    update: UserPasswordReset,

    current_user=Depends(
        require_roles("admin")
    ),
):

    user = await database[
        "users"
    ].find_one(
        {
            "username": username
        }
    )


    if user is None:

        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado",
        )


    # Para este MVP el admin no cambia
    # su propia contraseña desde aquí.

    if user.get("role") == "admin":

        raise HTTPException(
            status_code=400,
            detail=(
                "La contraseña del administrador "
                "no se modifica desde este módulo"
            ),
        )


    new_hash = hash_password(
        update.password
    )


    await database[
        "users"
    ].update_one(
        {
            "username": username
        },
        {
            "$set": {

                "password_hash":
                    new_hash,

                "updated_at":
                    datetime.now(
                        timezone.utc
                    ),

                "updated_by":
                    current_user[
                        "username"
                    ],
            }
        },
    )


    return {
        "message":
            "Contraseña actualizada correctamente"
    }