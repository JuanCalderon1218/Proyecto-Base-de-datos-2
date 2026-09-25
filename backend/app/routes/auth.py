from typing import Annotated

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
)
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Usuario o contraseña incorrectos"
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    access_token = create_access_token(
        {
            "sub": user["username"]
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


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