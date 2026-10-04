from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev

from backend.app.detection.config import (
    BEHAVIOR_MIN_SAMPLES,
    BEHAVIOR_Z_THRESHOLD,
    BUSINESS_UTC_OFFSET,
    FAILURE_THRESHOLD,
    FAILURE_WINDOW_MINUTES,
    HIGH_FREQUENCY_THRESHOLD,
    HIGH_FREQUENCY_WINDOW_SECONDS,
    UNUSUAL_HOUR_END,
    UNUSUAL_HOUR_START,
)


BUSINESS_TIMEZONE = timezone(
    timedelta(hours=BUSINESS_UTC_OFFSET)
)


def normalize_timestamp(timestamp: datetime) -> datetime:
    """
    Garantiza que el timestamp tenga zona horaria
    y lo convierte a UTC.
    """

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(
            tzinfo=timezone.utc
        )

    return timestamp.astimezone(timezone.utc)


def detect_mass_operation(event: dict):
    """
    Detecta DELETE o UPDATE con una gran cantidad
    de registros afectados.
    """

    operation = event["operation"]
    records = event["records_affected"]

    # DELETE extremadamente grande
    if operation == "DELETE" and records >= 1000:
        return {
            "type": "MASS_DELETE",
            "score": 75,
            "reason": (
                f"Se eliminaron {records} registros. "
                "La operación supera el límite crítico."
            ),
            "evidence": {
                "records_affected": records,
                "critical_threshold": 1000,
            },
        }

    # DELETE grande
    if operation == "DELETE" and records >= 200:
        return {
            "type": "MASS_DELETE",
            "score": 50,
            "reason": (
                f"Se eliminaron {records} registros. "
                "La operación supera el límite permitido."
            ),
            "evidence": {
                "records_affected": records,
                "threshold": 200,
            },
        }

    # UPDATE extremadamente grande
    if operation == "UPDATE" and records >= 2000:
        return {
            "type": "MASS_UPDATE",
            "score": 60,
            "reason": (
                f"Se modificaron {records} registros."
            ),
            "evidence": {
                "records_affected": records,
                "critical_threshold": 2000,
            },
        }

    # UPDATE grande
    if operation == "UPDATE" and records >= 500:
        return {
            "type": "MASS_UPDATE",
            "score": 40,
            "reason": (
                f"Se modificaron {records} registros."
            ),
            "evidence": {
                "records_affected": records,
                "threshold": 500,
            },
        }

    return None


def detect_unusual_hour(event: dict):
    """
    Detecta operaciones realizadas entre
    medianoche y las 06:00.
    """

    timestamp = event["timestamp"]

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(
            tzinfo=timezone.utc
        )

    local_time = timestamp.astimezone(
        BUSINESS_TIMEZONE
    )

    hour = local_time.hour

    if UNUSUAL_HOUR_START <= hour < UNUSUAL_HOUR_END:
        return {
            "type": "UNUSUAL_HOUR",
            "score": 20,
            "reason": (
                "La operación se realizó en un "
                f"horario inusual: "
                f"{local_time.strftime('%H:%M')}."
            ),
            "evidence": {
                "local_hour": hour,
                "usual_start": UNUSUAL_HOUR_END,
            },
        }

    return None


async def detect_high_frequency(
    event: dict,
    database,
):
    """
    Detecta demasiadas operaciones realizadas
    por el mismo usuario en 60 segundos.
    """

    timestamp = normalize_timestamp(
        event["timestamp"]
    )

    window_start = timestamp - timedelta(
        seconds=HIGH_FREQUENCY_WINDOW_SECONDS
    )

    count = await database["events"].count_documents(
        {
            "user_id": event["user_id"],
            "timestamp": {
                "$gte": window_start,
                "$lte": timestamp,
            },
        }
    )

    if count >= HIGH_FREQUENCY_THRESHOLD:

        if count >= 200:
            score = 70
        else:
            score = 50

        return {
            "type": "HIGH_FREQUENCY",
            "score": score,
            "reason": (
                f"El usuario realizó {count} "
                f"operaciones en "
                f"{HIGH_FREQUENCY_WINDOW_SECONDS} "
                "segundos."
            ),
            "evidence": {
                "operations": count,
                "window_seconds":
                    HIGH_FREQUENCY_WINDOW_SECONDS,
                "threshold":
                    HIGH_FREQUENCY_THRESHOLD,
            },
        }

    return None


async def detect_repeated_failures(
    event: dict,
    database,
):
    """
    Detecta múltiples operaciones fallidas
    durante una ventana de tiempo.
    """

    # Si esta operación fue correcta,
    # igualmente consultamos el histórico.
    # Esto permite detectar una secuencia
    # reciente de fallos.

    timestamp = normalize_timestamp(
        event["timestamp"]
    )

    window_start = timestamp - timedelta(
        minutes=FAILURE_WINDOW_MINUTES
    )

    count = await database["events"].count_documents(
        {
            "user_id": event["user_id"],
            "success": False,
            "timestamp": {
                "$gte": window_start,
                "$lte": timestamp,
            },
        }
    )

    if count >= FAILURE_THRESHOLD:

        if count >= 10:
            score = 50
        else:
            score = 35

        return {
            "type": "REPEATED_FAILURES",
            "score": score,
            "reason": (
                f"Se detectaron {count} operaciones "
                f"fallidas en los últimos "
                f"{FAILURE_WINDOW_MINUTES} minutos."
            ),
            "evidence": {
                "failed_operations": count,
                "window_minutes":
                    FAILURE_WINDOW_MINUTES,
                "threshold":
                    FAILURE_THRESHOLD,
            },
        }

    return None


async def detect_behavior_deviation(
    event: dict,
    database,
    current_event_id,
):
    """
    Compara la cantidad de registros afectados
    con el comportamiento histórico del usuario.

    Se utiliza media y desviación estándar.
    """

    cursor = (
        database["events"]
        .find(
            {
                "_id": {
                    "$ne": current_event_id
                },
                "user_id": event["user_id"],
                "operation": event["operation"],
                "success": True,
            },
            {
                "records_affected": 1,
                "_id": 0,
            },
        )
        .sort("timestamp", -1)
        .limit(50)
    )

    history = await cursor.to_list(
        length=50
    )

    if len(history) < BEHAVIOR_MIN_SAMPLES:
        return None

    values = [
        item["records_affected"]
        for item in history
    ]

    average = mean(values)
    deviation = pstdev(values)

    current_value = event[
        "records_affected"
    ]

    # Evitamos división entre cero.
    if deviation == 0:

        if (
            average > 0
            and current_value >= average * 3
        ):
            return {
                "type": "BEHAVIOR_DEVIATION",
                "score": 30,
                "reason": (
                    "La cantidad de registros "
                    "afectados es muy diferente "
                    "al comportamiento habitual."
                ),
                "evidence": {
                    "current": current_value,
                    "average": round(
                        average,
                        2,
                    ),
                    "samples": len(values),
                },
            }

        return None

    z_score = (
        current_value - average
    ) / deviation

    if z_score >= BEHAVIOR_Z_THRESHOLD:
        return {
            "type": "BEHAVIOR_DEVIATION",
            "score": 30,
            "reason": (
                "La operación se aleja "
                "significativamente del "
                "comportamiento habitual."
            ),
            "evidence": {
                "current": current_value,
                "average": round(
                    average,
                    2,
                ),
                "standard_deviation": round(
                    deviation,
                    2,
                ),
                "z_score": round(
                    z_score,
                    2,
                ),
                "samples": len(values),
            },
        }

    return None