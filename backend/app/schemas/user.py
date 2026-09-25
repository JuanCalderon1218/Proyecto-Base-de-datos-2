from typing import Literal

from pydantic import BaseModel, Field


class UserPublic(BaseModel):
    username: str
    role: Literal["admin", "analyst"]
    active: bool


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role: Literal["analyst"] = "analyst"


class UserActiveUpdate(BaseModel):
    active: bool


class UserPasswordReset(BaseModel):
    password: str = Field(
        min_length=8,
        max_length=128,
    )