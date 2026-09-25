from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.auth.security import get_current_user

from backend.app.database.connection import (
    database,
)
from backend.app.detection.engine import (
    analyze_event,
)
from backend.app.schemas.event import (
    EventCreate,
)
from backend.app.services.alert_service import (
    create_or_merge_alert,
)


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    event: EventCreate,
):
    document = event.model_dump()

    document["event_id"] = (
        f"EVT-{uuid4().hex[:8].upper()}"
    )

    document["analyzed"] = False

    # -------------------------
    # Guardar evento
    # -------------------------

    result = await database[
        "events"
    ].insert_one(document)

    mongo_id = result.inserted_id

    # -------------------------
    # Analizar evento
    # -------------------------

    analysis = await analyze_event(
        document,
        mongo_id,
    )

    alert_id = None
    alert_merged = False

    # -------------------------
    # Generar alerta
    # -------------------------

    if analysis["is_anomalous"]:

        alert_result = (
            await create_or_merge_alert(
                document,
                analysis,
            )
        )

        alert_id = alert_result[
            "alert_id"
        ]

        alert_merged = alert_result[
            "merged"
        ]

    # -------------------------
    # Marcar evento analizado
    # -------------------------

    await database["events"].update_one(
        {
            "_id": mongo_id
        },
        {
            "$set": {
                "analyzed": True,
                "is_anomalous":
                    analysis[
                        "is_anomalous"
                    ],
                "anomaly_score":
                    analysis["score"],
                "severity":
                    analysis["severity"],
                "alert_id":
                    alert_id,
            }
        },
    )

    document.pop("_id", None)

    document.update(
        {
            "analyzed": True,
            "is_anomalous":
                analysis["is_anomalous"],
            "anomaly_score":
                analysis["score"],
            "severity":
                analysis["severity"],
            "alert_id":
                alert_id,
        }
    )

    document["analysis"] = {
        "is_anomalous":
            analysis["is_anomalous"],

        "score":
            analysis["score"],

        "severity":
            analysis["severity"],

        "detections":
            analysis["detections"],

        "alert_id":
            alert_id,

        "alert_merged":
            alert_merged,
    }

    return document


@router.get("")
async def get_events(
    user_id: str | None = None,
    operation: str | None = None,
    anomalous: bool | None = None,
    success: bool | None = None,
    limit: int = Query(
        default=100,
        ge=1,
        le=500),
    current_user=Depends(get_current_user),
):
    query = {}

    if user_id:
        query["user_id"] = user_id

    if operation:
        query["operation"] = operation

    if anomalous is not None:
        query["is_anomalous"] = anomalous

    if success is not None:
        query["success"] = success

    events = []

    cursor = (
        database["events"]
        .find(query)
        .sort("timestamp", -1)
        .limit(limit)
    )

    async for document in cursor:
        document["_id"] = str(
            document["_id"]
        )

        events.append(document)

    return events


@router.get("/{event_id}")
async def get_event(
    event_id: str,
current_user=Depends(get_current_user),
):
    event = await database[
        "events"
    ].find_one(
        {
            "event_id": event_id
        }
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Evento no encontrado",
        )

    event["_id"] = str(
        event["_id"]
    )

    return event