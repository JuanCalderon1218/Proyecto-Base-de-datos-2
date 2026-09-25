from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from backend.app.auth.security import get_current_user
from backend.app.database.connection import database
from backend.app.detection.config import BUSINESS_UTC_OFFSET


router = APIRouter(
    prefix="/analysis",
    tags=["Activity Analysis"],
)


BUSINESS_TIMEZONE = timezone(
    timedelta(hours=BUSINESS_UTC_OFFSET)
)

OPERATIONS = [
    "READ",
    "INSERT",
    "UPDATE",
    "DELETE",
]


def to_local_datetime(
    value: datetime,
) -> datetime:
    """
    Convierte timestamps almacenados en MongoDB
    a la zona horaria utilizada por el sistema.
    """

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        BUSINESS_TIMEZONE
    )


def calculate_variation(
    current: float,
    historical_average: float,
):
    """
    Calcula variación porcentual.

    Si no existe base histórica suficiente,
    devuelve None.
    """

    if historical_average == 0:

        if current == 0:
            return 0.0

        return None

    return round(
        (
            (
                current
                - historical_average
            )
            / historical_average
        )
        * 100,
        1,
    )


# ==========================================
# USUARIOS DISPONIBLES
# ==========================================

@router.get("/users")
async def get_analysis_users(
    current_user=Depends(get_current_user),
):
    users = await database["events"].distinct(
        "user_id"
    )

    clean_users = sorted(
        [
            user
            for user in users
            if isinstance(user, str)
            and user.strip()
        ]
    )

    return {
        "users": clean_users,
        "count": len(clean_users),
    }


# ==========================================
# ANÁLISIS DE UN USUARIO EN UN DÍA
# ==========================================

@router.get(
    "/user/{user_id}/day"
)
async def analyze_user_day(
    user_id: str,

    selected_date: date = Query(
        ...,
        alias="date",
        description="Fecha YYYY-MM-DD",
    ),

    history_days: int = Query(
        default=7,
        ge=1,
        le=30,
    ),

    current_user=Depends(
        get_current_user
    ),
):

    # --------------------------------------
    # Intervalo del día seleccionado
    # --------------------------------------

    start_local = datetime.combine(
        selected_date,
        time.min,
        tzinfo=BUSINESS_TIMEZONE,
    )

    end_local = (
        start_local
        + timedelta(days=1)
    )

    start_utc = start_local.astimezone(
        timezone.utc
    )

    end_utc = end_local.astimezone(
        timezone.utc
    )


    # --------------------------------------
    # Eventos del día seleccionado
    # --------------------------------------

    cursor = (
        database["events"]
        .find(
            {
                "user_id": user_id,

                "timestamp": {
                    "$gte": start_utc,
                    "$lt": end_utc,
                },
            }
        )
        .sort(
            "timestamp",
            1,
        )
    )


    events = []

    operations = {
        operation: 0
        for operation in OPERATIONS
    }

    hourly_activity = [
        0
        for _ in range(24)
    ]

    total_events = 0
    successful_events = 0
    failed_events = 0
    anomalous_events = 0
    records_affected = 0

    unusual_hour_events = 0


    async for event in cursor:

        total_events += 1

        operation = event.get(
            "operation"
        )

        if operation in operations:
            operations[operation] += 1


        if event.get(
            "success",
            False,
        ):
            successful_events += 1

        else:
            failed_events += 1


        if event.get(
            "is_anomalous",
            False,
        ):
            anomalous_events += 1


        records_affected += (
            event.get(
                "records_affected",
                0,
            )
            or 0
        )


        timestamp = event.get(
            "timestamp"
        )

        local_timestamp = None

        if timestamp:

            local_timestamp = (
                to_local_datetime(
                    timestamp
                )
            )

            hourly_activity[
                local_timestamp.hour
            ] += 1

            if (
                0
                <= local_timestamp.hour
                < 6
            ):
                unusual_hour_events += 1


        events.append(
            {
                "event_id":
                    event.get(
                        "event_id"
                    ),

                "timestamp":
                    (
                        local_timestamp.isoformat()
                        if local_timestamp
                        else None
                    ),

                "operation":
                    operation,

                "collection":
                    event.get(
                        "collection"
                    ),

                "records_affected":
                    event.get(
                        "records_affected",
                        0,
                    ),

                "success":
                    event.get(
                        "success",
                        False,
                    ),

                "is_anomalous":
                    event.get(
                        "is_anomalous",
                        False,
                    ),

                "severity":
                    event.get(
                        "severity"
                    ),

                "alert_id":
                    event.get(
                        "alert_id"
                    ),
            }
        )


    # --------------------------------------
    # Comportamiento histórico
    # --------------------------------------

    history_start_local = (
        start_local
        - timedelta(
            days=history_days
        )
    )

    history_start_utc = (
        history_start_local
        .astimezone(
            timezone.utc
        )
    )


    history_cursor = (
        database["events"]
        .find(
            {
                "user_id": user_id,

                "timestamp": {
                    "$gte":
                        history_start_utc,

                    "$lt":
                        start_utc,
                },
            }
        )
    )


    # Creamos todos los días,
    # incluso si no hubo actividad.

    historical_days = {}

    for days_back in range(
        history_days,
        0,
        -1,
    ):

        historical_date = (
            selected_date
            - timedelta(
                days=days_back
            )
        )

        historical_days[
            historical_date.isoformat()
        ] = {
            "events": 0,

            "operations": {
                operation: 0
                for operation in OPERATIONS
            },
        }


    async for event in history_cursor:

        timestamp = event.get(
            "timestamp"
        )

        if not timestamp:
            continue

        local_timestamp = (
            to_local_datetime(
                timestamp
            )
        )

        day_key = (
            local_timestamp
            .date()
            .isoformat()
        )

        if day_key not in historical_days:
            continue


        historical_days[
            day_key
        ]["events"] += 1


        operation = event.get(
            "operation"
        )

        if operation in OPERATIONS:

            historical_days[
                day_key
            ]["operations"][
                operation
            ] += 1


    # --------------------------------------
    # Promedios
    # --------------------------------------

    average_total_events = round(
        sum(
            day["events"]
            for day
            in historical_days.values()
        )
        / history_days,
        2,
    )


    operation_averages = {}

    for operation in OPERATIONS:

        operation_averages[
            operation
        ] = round(
            sum(
                day["operations"][
                    operation
                ]
                for day
                in historical_days.values()
            )
            / history_days,
            2,
        )


    total_variation = (
        calculate_variation(
            total_events,
            average_total_events,
        )
    )


    operation_variations = {}

    for operation in OPERATIONS:

        operation_variations[
            operation
        ] = calculate_variation(
            operations[
                operation
            ],
            operation_averages[
                operation
            ],
        )


    # --------------------------------------
    # Cambios relevantes
    # --------------------------------------

    changes = []


    if (
        total_variation is not None
        and total_variation >= 50
    ):

        changes.append(
            (
                "La actividad total aumentó "
                f"{total_variation}% respecto "
                f"al promedio de los "
                f"{history_days} días anteriores."
            )
        )


    elif (
        total_variation is not None
        and total_variation <= -50
    ):

        changes.append(
            (
                "La actividad total disminuyó "
                f"{abs(total_variation)}% respecto "
                f"al promedio de los "
                f"{history_days} días anteriores."
            )
        )


    for operation in OPERATIONS:

        variation = (
            operation_variations[
                operation
            ]
        )

        if (
            variation is not None
            and variation >= 100
            and operations[operation] > 0
        ):

            changes.append(
                (
                    f"La operación {operation} "
                    f"aumentó {variation}% respecto "
                    "a su promedio histórico."
                )
            )


        elif (
            variation is None
            and operations[operation] > 0
            and operation_averages[
                operation
            ] == 0
        ):

            changes.append(
                (
                    f"Se registró actividad "
                    f"{operation}, aunque no hubo "
                    f"operaciones de ese tipo durante "
                    f"los {history_days} días anteriores."
                )
            )


    if anomalous_events > 0:

        changes.append(
            (
                f"Se detectaron "
                f"{anomalous_events} eventos "
                "anómalos durante el día."
            )
        )


    if failed_events > 0:

        changes.append(
            (
                f"Se registraron "
                f"{failed_events} operaciones "
                "fallidas."
            )
        )


    if unusual_hour_events > 0:

        changes.append(
            (
                f"Se registraron "
                f"{unusual_hour_events} operaciones "
                "entre las 00:00 y las 05:59."
            )
        )


    # --------------------------------------
    # Actividad por hora
    # --------------------------------------

    hourly_result = [
        {
            "hour": f"{hour:02d}:00",
            "events":
                hourly_activity[hour],
        }

        for hour in range(24)
    ]


    # --------------------------------------
    # Histórico diario
    # --------------------------------------

    historical_result = [
        {
            "date": day_key,
            "events":
                value["events"],
        }

        for day_key, value
        in historical_days.items()
    ]


    # --------------------------------------
    # Respuesta
    # --------------------------------------

    return {

        "user_id": user_id,

        "date":
            selected_date.isoformat(),

        "summary": {

            "total_events":
                total_events,

            "successful_events":
                successful_events,

            "failed_events":
                failed_events,

            "anomalous_events":
                anomalous_events,

            "records_affected":
                records_affected,
        },


        "operations":
            operations,


        "hourly_activity":
            hourly_result,


        "comparison": {

            "history_days":
                history_days,

            "average_total_events":
                average_total_events,

            "total_variation_percent":
                total_variation,

            "operation_averages":
                operation_averages,

            "operation_variations":
                operation_variations,

            "daily_history":
                historical_result,
        },


        "changes":
            changes,


        "events":
            events,
    }