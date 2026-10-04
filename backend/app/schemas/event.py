from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    user_id: str = Field(min_length=1)

    operation: Literal[
        "READ",
        "INSERT",
        "UPDATE",
        "DELETE"
    ]

    collection: str = Field(min_length=1)

    records_affected: int = Field(ge=0)

    success: bool

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )