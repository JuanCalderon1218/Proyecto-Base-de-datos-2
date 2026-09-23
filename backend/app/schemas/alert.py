from typing import Literal

from pydantic import BaseModel


class AlertStatusUpdate(BaseModel):
    status: Literal[
        "pending",
        "reviewed",
        "resolved",
    ]