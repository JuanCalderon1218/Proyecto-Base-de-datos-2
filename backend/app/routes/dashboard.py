from fastapi import APIRouter
from fastapi import APIRouter, Depends

from backend.app.auth.security import get_current_user

from backend.app.database.connection import database
from fastapi import (
    APIRouter,
    Depends,
)

from backend.app.auth.security import (
    get_current_user,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
async def dashboard_summary(
    current_user=Depends(
        get_current_user),
):
    total_events = await database[
        "events"
    ].count_documents({})

    anomalous_events = await database[
        "events"
    ].count_documents(
        {
            "is_anomalous": True
        }
    )

    total_alerts = await database[
        "alerts"
    ].count_documents({})

    pending_alerts = await database[
        "alerts"
    ].count_documents(
        {
            "status": "pending"
        }
    )

    critical_alerts = await database[
        "alerts"
    ].count_documents(
        {
            "severity": "critical"
        }
    )

    reviewed_alerts = await database[
        "alerts"
    ].count_documents(
        {
            "status": "reviewed"
        }
    )

    resolved_alerts = await database[
        "alerts"
    ].count_documents(
        {
            "status": "resolved"
        }
    )

    return {
        "events": {
            "total": total_events,
            "anomalous": anomalous_events,
        },
        "alerts": {
            "total": total_alerts,
            "pending": pending_alerts,
            "reviewed": reviewed_alerts,
            "resolved": resolved_alerts,
            "critical": critical_alerts,
        },
    }