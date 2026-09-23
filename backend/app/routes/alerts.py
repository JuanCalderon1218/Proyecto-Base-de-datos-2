from fastapi import APIRouter, HTTPException

from backend.app.database.connection import (
    database,
)


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.get("")
async def get_alerts():
    alerts = []

    cursor = (
        database["alerts"]
        .find()
        .sort("created_at", -1)
        .limit(100)
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