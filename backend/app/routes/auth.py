from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import uuid4

import jwt

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
)

from backend.app.auth.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    oauth2_scheme,
)
from backend.app.config.settings import settings
from backend.app.database.connection import database
from backend.app.observability import logger
from backend.app.schemas.auth import Token
from backend.app.schemas.user import UserPublic


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=Token,
)
async def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
):

    user = await authenticate_user(
        form_data.username,
        form_data.password,
    )

    if user is None:
        logger.warning(
            "login_failed username=%s",
            form_data.username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Usuario o contraseña incorrectos"
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    session_id = (
        f"SES-{uuid4().hex[:8].upper()}"
    )

    started_at = datetime.now(timezone.utc)
    expires_at = started_at + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    await database["sessions"].insert_one(
        {
            "session_id": session_id,
            "username": user["username"],
            "role": user["role"],
            "started_at": started_at,
            "expires_at": expires_at,
            "ended_at": None,
            "status": "active",
        }
    )

    access_token = create_access_token(
        {
            "sub": user["username"],
            "sid": session_id,
        }
    )

    logger.info(
        "login_success username=%s session_id=%s",
        user["username"],
        session_id,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    current_user=Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    session_id = payload.get("sid")
    session = await database["sessions"].find_one(
        {
            "session_id": session_id,
            "username": current_user["username"],
            "status": "active",
        }
    )

    if session is not None:
        await database["sessions"].update_one(
            {
                "_id": session["_id"]
            },
            {
                "$set": {
                    "status": "closed",
                    "ended_at": datetime.now(
                        timezone.utc
                    ),
                }
            },
        )

        logger.info(
            "logout username=%s session_id=%s",
            current_user["username"],
            session["session_id"],
        )

    return {
        "status": "ok"
    }


@router.get("/sessions/me")
async def my_sessions(
    current_user=Depends(get_current_user),
):
    sessions = []

    cursor = (
        database["sessions"]
        .find(
            {
                "username": current_user["username"]
            },
            {
                "_id": 0
            },
        )
        .sort("started_at", -1)
        .limit(20)
    )

    async for session in cursor:
        sessions.append(session)

    return sessions


@router.get(
    "/me",
    response_model=UserPublic,
)
async def get_me(
    current_user=Depends(
        get_current_user
    ),
):

    return {
        "username":
            current_user["username"],
        "role":
            current_user["role"],
        "active":
            current_user["active"],
    }
