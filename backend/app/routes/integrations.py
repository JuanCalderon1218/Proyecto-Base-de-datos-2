from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from backend.app.auth.security import require_roles
from backend.app.database.connection import database
from backend.app.observability import logger
from backend.app.services.integrations import (
    create_github_issue,
    send_discord_alert,
)


router = APIRouter(
    prefix="/integrations",
    tags=["Integrations"],
)


async def get_alert_or_404(
    alert_id: str,
):
    alert = await database["alerts"].find_one(
        {
            "alert_id": alert_id
        }
    )

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail="Alerta no encontrada",
        )

    return alert


async def save_history(
    alert_id: str,
    provider: str,
    result: dict,
    username: str,
):
    await database[
        "integration_history"
    ].insert_one(
        {
            "alert_id": alert_id,
            "provider": provider,
            "result": result,
            "executed_by": username,
            "created_at": datetime.now(
                timezone.utc
            ),
        }
    )


@router.post("/github/{alert_id}")
async def github_issue(
    alert_id: str,
    current_user=Depends(
        require_roles("admin", "analyst")
    ),
):
    alert = await get_alert_or_404(
        alert_id
    )

    try:
        result = await create_github_issue(
            alert
        )
    except Exception as exc:
        logger.exception(
            "github_integration_failed alert_id=%s",
            alert_id,
        )
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    await save_history(
        alert_id,
        "github",
        result,
        current_user["username"],
    )

    logger.info(
        "github_issue_created alert_id=%s",
        alert_id,
    )

    return result


@router.post("/discord/{alert_id}")
async def discord_notification(
    alert_id: str,
    current_user=Depends(
        require_roles("admin", "analyst")
    ),
):
    alert = await get_alert_or_404(
        alert_id
    )

    try:
        result = await send_discord_alert(
            alert
        )
    except Exception as exc:
        logger.exception(
            "discord_integration_failed alert_id=%s",
            alert_id,
        )
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    await save_history(
        alert_id,
        "discord",
        result,
        current_user["username"],
    )

    logger.info(
        "discord_notification_sent alert_id=%s",
        alert_id,
    )

    return result


@router.get("/history")
async def integration_history(
    current_user=Depends(
        require_roles("admin", "analyst")
    ),
):
    rows = []

    cursor = (
        database["integration_history"]
        .find(
            {},
            {
                "_id": 0
            },
        )
        .sort("created_at", -1)
        .limit(100)
    )

    async for item in cursor:
        rows.append(item)

    return rows
