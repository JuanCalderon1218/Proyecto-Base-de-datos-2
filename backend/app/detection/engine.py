from backend.app.database.connection import (
    database,
)
from backend.app.detection.rules import (
    detect_behavior_deviation,
    detect_high_frequency,
    detect_mass_operation,
    detect_repeated_failures,
    detect_unusual_hour,
)


def calculate_severity(score: int):
    """
    Convierte la puntuación en severidad.
    """

    if score <= 0:
        return None

    if score < 25:
        return "low"

    if score < 50:
        return "medium"

    if score < 75:
        return "high"

    return "critical"


async def analyze_event(
    event: dict,
    current_event_id,
):
    """
    Ejecuta todas las reglas de detección.
    """

    detections = []

    # -------------------------
    # Operación masiva
    # -------------------------

    result = detect_mass_operation(event)

    if result:
        detections.append(result)

    # -------------------------
    # Horario inusual
    # -------------------------

    result = detect_unusual_hour(event)

    if result:
        detections.append(result)

    # -------------------------
    # Alta frecuencia
    # -------------------------

    result = await detect_high_frequency(
        event,
        database,
    )

    if result:
        detections.append(result)

    # -------------------------
    # Fallos repetidos
    # -------------------------

    result = await detect_repeated_failures(
        event,
        database,
    )

    if result:
        detections.append(result)

    # -------------------------
    # Desviación estadística
    # -------------------------

    result = await detect_behavior_deviation(
        event,
        database,
        current_event_id,
    )

    if result:
        detections.append(result)

    score = min(
        sum(
            detection["score"]
            for detection in detections
        ),
        100,
    )

    severity = calculate_severity(score)

    return {
        "is_anomalous": len(detections) > 0,
        "score": score,
        "severity": severity,
        "detections": detections,
    }