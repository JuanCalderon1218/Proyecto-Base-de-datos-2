from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.database.connection import database
from backend.app.detection.config import ALERT_MERGE_MINUTES


async def create_or_merge_alert(
    event: dict,
    analysis: dict,
):
    """
    Crea una nueva alerta o agrupa una detección
    con una alerta reciente equivalente.
    """

    now = datetime.now(timezone.utc)

    detection_types = sorted(
        detection["type"]
        for detection in analysis["detections"]
    )

    signature = "|".join(detection_types)

    merge_window = now - timedelta(
        minutes=ALERT_MERGE_MINUTES
    )

    existing_alert = await database["alerts"].find_one(
        {
            "user_id": event["user_id"],
            "signature": signature,
            "status": "pending",
            "created_at": {
                "$gte": merge_window
            },
        }
    )

    reasons = [
        detection["reason"]
        for detection in analysis["detections"]
    ]

    # Si ya existe una alerta reciente equivalente,
    # actualizamos esa alerta.
    if existing_alert:

        await database["alerts"].update_one(
            {
                "_id": existing_alert["_id"]
            },
            {
                "$inc": {
                    "occurrence_count": 1
                },
                "$set": {
                    "latest_event_id": event["event_id"],
                    "score": analysis["score"],
                    "severity": analysis["severity"],
                    "reasons": reasons,
                    "detections": analysis["detections"],
                    "updated_at": now,
                },
            },
        )

        return {
            "alert_id": existing_alert["alert_id"],
            "merged": True,
        }

    # Si no existe, creamos una nueva alerta.
    alert_id = f"ALT-{uuid4().hex[:8].upper()}"

    alert_document = {
        "alert_id": alert_id,
        "event_id": event["event_id"],
        "latest_event_id": event["event_id"],
        "user_id": event["user_id"],
        "operation": event["operation"],
        "collection": event["collection"],
        "records_affected": event["records_affected"],
        "types": detection_types,
        "signature": signature,
        "score": analysis["score"],
        "severity": analysis["severity"],
        "reasons": reasons,
        "detections": analysis["detections"],
        "status": "pending",
        "occurrence_count": 1,
        "event_timestamp": event["timestamp"],
        "created_at": now,
        "updated_at": now,
    }

    await database["alerts"].insert_one(
        alert_document
    )

    return {
        "alert_id": alert_id,
        "merged": False,
    }