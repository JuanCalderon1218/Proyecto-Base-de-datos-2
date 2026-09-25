from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from backend.app.auth.security import get_current_user
from fastapi import APIRouter, Query

from backend.app.database.connection import database
from backend.app.detection.config import BUSINESS_UTC_OFFSET


router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
)


# ---------------------------------
# Zona horaria para MongoDB
# ---------------------------------

sign = "+" if BUSINESS_UTC_OFFSET >= 0 else "-"

BUSINESS_MONGO_TIMEZONE = (
    f"{sign}{abs(BUSINESS_UTC_OFFSET):02d}:00"
)


# ---------------------------------
# Alertas por severidad
# ---------------------------------

@router.get("/alerts-by-severity")
async def alerts_by_severity(current_user=Depends(get_current_user)):

    pipeline = [
        {
            "$group": {
                "_id": "$severity",
                "count": {
                    "$sum": 1
                },
            }
        }
    ]

    # En PyMongo Async aggregate necesita await
    cursor = await database["alerts"].aggregate(
        pipeline
    )

    # Dejamos siempre las 4 categorías,
    # aunque alguna tenga 0 alertas.
    counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }

    async for item in cursor:
        severity = item.get("_id")

        if severity in counts:
            counts[severity] = item["count"]

    return [
        {
            "severity": severity,
            "count": count,
        }
        for severity, count in counts.items()
    ]


# ---------------------------------
# Eventos por tipo de operación
# ---------------------------------

@router.get("/events-by-operation")
async def events_by_operation(current_user=Depends(get_current_user)):

    pipeline = [
        {
            "$group": {
                "_id": "$operation",
                "count": {
                    "$sum": 1
                },
            }
        }
    ]

    cursor = await database["events"].aggregate(
        pipeline
    )

    counts = {
        "READ": 0,
        "INSERT": 0,
        "UPDATE": 0,
        "DELETE": 0,
    }

    async for item in cursor:
        operation = item.get("_id")

        if operation in counts:
            counts[operation] = item["count"]

    return [
        {
            "operation": operation,
            "count": count,
        }
        for operation, count in counts.items()
    ]


# ---------------------------------
# Actividad por usuario
# ---------------------------------

@router.get("/activity-by-user")
async def activity_by_user(
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
current_user=Depends(get_current_user)
):

    pipeline = [
        {
            "$group": {
                "_id": "$user_id",

                "events": {
                    "$sum": 1
                },

                "anomalies": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": [
                                    "$is_anomalous",
                                    True,
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {
            "$sort": {
                "events": -1
            }
        },
        {
            "$limit": limit
        },
    ]

    cursor = await database["events"].aggregate(
        pipeline
    )

    result = []

    async for item in cursor:

        result.append(
            {
                "user_id": item.get(
                    "_id",
                    "desconocido",
                ),
                "events": item.get(
                    "events",
                    0,
                ),
                "anomalies": item.get(
                    "anomalies",
                    0,
                ),
            }
        )

    return result


# ---------------------------------
# Actividad diaria
# ---------------------------------

@router.get("/daily-activity")
async def daily_activity(
    days: int = Query(
        default=7,
        ge=1,
        le=90,
    ),
current_user=Depends(get_current_user)
):

    # Creamos la zona horaria local
    local_timezone = timezone(
        timedelta(
            hours=BUSINESS_UTC_OFFSET
        )
    )

    # Fecha/hora actual en la zona configurada
    now_local = datetime.now(
        local_timezone
    )

    # Inicio del primer día solicitado
    start_local = (
        now_local
        - timedelta(days=days - 1)
    ).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    # Convertimos a UTC para consultar MongoDB
    start_utc = start_local.astimezone(
        timezone.utc
    )

    pipeline = [
        {
            "$match": {
                "timestamp": {
                    "$gte": start_utc
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp",
                        "timezone":
                            BUSINESS_MONGO_TIMEZONE,
                    }
                },

                "events": {
                    "$sum": 1
                },

                "anomalies": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": [
                                    "$is_anomalous",
                                    True,
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        },
    ]

    cursor = await database["events"].aggregate(
        pipeline
    )

    database_results = {}

    async for item in cursor:

        database_results[
            item["_id"]
        ] = {
            "events": item.get(
                "events",
                0,
            ),
            "anomalies": item.get(
                "anomalies",
                0,
            ),
        }

    # Agregamos también los días sin datos
    result = []

    for i in range(days):

        current_date = (
            start_local
            + timedelta(days=i)
        )

        date_string = current_date.strftime(
            "%Y-%m-%d"
        )

        values = database_results.get(
            date_string,
            {
                "events": 0,
                "anomalies": 0,
            },
        )

        result.append(
            {
                "date": date_string,
                "events": values["events"],
                "anomalies":
                    values["anomalies"],
            }
        )

    return result