from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from backend.app.database.connection import database
from backend.app.schemas.alert import AlertStatusUpdate


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.get("")
async def get_alerts(
    severity: str | None = None,
    status: str | None = None,
    user_id: str | None = None,
    operation: str | None = None,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
):
    query = {}

    if severity:
        query["severity"] = severity

    if status:
        query["status"] = status

    if user_id:
        query["user_id"] = user_id

    if operation:
        query["operation"] = operation

    alerts = []

    cursor = (
        database["alerts"]
        .find(query)
        .sort("created_at", -1)
        .limit(limit)
    )

    async for alert in cursor:
        alert["_id"] = str(
            alert["_id"]
        )

        alerts.append(alert)

    return alerts


@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
):
    alert = await database[
        "alerts"
    ].find_one(
        {
            "alert_id": alert_id
        }
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alerta no encontrada",
        )

    alert["_id"] = str(
        alert["_id"]
    )

    return alert


@router.patch("/{alert_id}/status")
async def update_alert_status(
    alert_id: str,
    data: AlertStatusUpdate,
):
    alert = await database[
        "alerts"
    ].find_one(
        {
            "alert_id": alert_id
        }
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alerta no encontrada",
        )

    await database["alerts"].update_one(
        {
            "alert_id": alert_id
        },
        {
            "$set": {
                "status": data.status,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    return {
        "message": (
            "Estado actualizado correctamente"
        ),
        "alert_id": alert_id,
        "status": data.status,
    }