from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from backend.app.config.settings import settings
from backend.app.database.connection import database


# ---------------------------------
# Configuración
# ---------------------------------

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# ---------------------------------
# Contraseñas
# ---------------------------------

def hash_password(
    password: str,
) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


# ---------------------------------
# Autenticación
# ---------------------------------

async def authenticate_user(
    username: str,
    password: str,
):
    user = await database["users"].find_one(
        {
            "username": username
        }
    )

    if user is None:
        return None

    if not user.get("active", False):
        return None

    if not verify_password(
        password,
        user["password_hash"],
    ):
        return None

    return user


# ---------------------------------
# JWT
# ---------------------------------

def create_access_token(
    data: dict,
) -> str:

    payload = data.copy()

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload["exp"] = expire

    encoded_token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_token


# ---------------------------------
# Usuario autenticado
# ---------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no válidas",
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[
                settings.jwt_algorithm
            ],
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    user = await database[
        "users"
    ].find_one(
        {
            "username": username,
            "active": True,
        }
    )

    if user is None:
        raise credentials_exception

    return user


# ---------------------------------
# Control de roles
# ---------------------------------

def require_roles(
    *allowed_roles: str,
):

    async def role_checker(
        current_user=Depends(
            get_current_user
        ),
    ):

        if (
            current_user["role"]
            not in allowed_roles
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "No tienes permisos "
                    "para realizar esta acción"
                ),
            )

        return current_user

    return role_checker