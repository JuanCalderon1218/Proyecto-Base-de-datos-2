from uuid import uuid4

from fastapi import APIRouter, status

from backend.app.database.connection import database
from backend.app.schemas.event import EventCreate


router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED
)
async def create_event(event: EventCreate):
    document = event.model_dump()

    document["event_id"] = (
        f"EVT-{uuid4().hex[:8].upper()}"
    )

    await database["events"].insert_one(document)

    document.pop("_id", None)

    return document


@router.get("")
async def get_events():
    events = []

    cursor = (
        database["events"]
        .find()
        .sort("timestamp", -1)
        .limit(100)
    )

    async for document in cursor:
        document["_id"] = str(document["_id"])
        events.append(document)

    return events