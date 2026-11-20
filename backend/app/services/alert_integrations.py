from datetime import datetime, timezone

from backend.app.config.settings import settings
from backend.app.database.connection import database
from backend.app.observability import logger
from backend.app.services.integrations import (
    create_github_issue,
    send_discord_alert,
)


GITHUB_ISSUE_SEVERITIES = {"high", "critical"}


async def _save_history(
    alert_id: str,
    provider: str,
    status: str,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    """Registra el resultado de cada intento de integración."""
    try:
        await database["integration_history"].insert_one(
            {
                "alert_id": alert_id,
                "provider": provider,
                "status": status,
                "result": result or {},
                "error": error,
                "executed_by": "system",
                "created_at": datetime.now(timezone.utc),
            }
        )
    except Exception:
        # Un fallo al guardar el historial no debe interrumpir
        # la recepción ni el análisis del evento.
        logger.exception(
            "integration_history_save_failed alert_id=%s provider=%s",
            alert_id,
            provider,
        )


async def dispatch_alert_integrations(alert_id: str) -> dict:
    """
    Envía Discord para cada alerta nueva y crea GitHub Issues
    solamente para severidad high o critical.

    Los fallos de servicios externos se registran, pero nunca
    cancelan la creación de la alerta ni la respuesta de ingesta.
    """
    alert = await database["alerts"].find_one(
        {"alert_id": alert_id}
    )
    if alert is None:
        logger.error("integration_alert_not_found alert_id=%s", alert_id)
        return {"status": "skipped", "reason": "alert_not_found"}

    outcomes = {}
    severity = str(alert.get("severity") or "").lower()

    # Discord: notificar cada alerta nueva si hay webhook configurado.
    if not settings.discord_webhook_url:
        outcomes["discord"] = {"status": "skipped", "reason": "webhook_not_configured"}
        await _save_history(
            alert_id,
            "discord",
            "skipped",
            error="DISCORD_WEBHOOK_URL no esta configurado",
        )
    else:
        try:
            result = await send_discord_alert(alert)
            outcomes["discord"] = {"status": "sent", **result}
            await _save_history(alert_id, "discord", "sent", result=result)
            logger.info("discord_auto_notification_sent alert_id=%s", alert_id)
        except Exception as exc:
            outcomes["discord"] = {"status": "failed", "error": str(exc)}
            await _save_history(
                alert_id,
                "discord",
                "failed",
                error=str(exc)[:1000],
            )
            logger.exception("discord_auto_notification_failed alert_id=%s", alert_id)

    # GitHub: abrir una incidencia solo para alertas altas o críticas.
    if severity not in GITHUB_ISSUE_SEVERITIES:
        outcomes["github"] = {
            "status": "skipped",
            "reason": "severity_below_high",
        }
        await _save_history(
            alert_id,
            "github",
            "skipped",
            error="La severidad no alcanza high o critical",
        )
    elif not settings.github_token:
        outcomes["github"] = {
            "status": "skipped",
            "reason": "token_not_configured",
        }
        await _save_history(
            alert_id,
            "github",
            "skipped",
            error="GITHUB_TOKEN no esta configurado",
        )
    else:
        try:
            result = await create_github_issue(alert)
            outcomes["github"] = {"status": "created", **result}
            await _save_history(alert_id, "github", "created", result=result)
            logger.info("github_auto_issue_created alert_id=%s", alert_id)
        except Exception as exc:
            outcomes["github"] = {"status": "failed", "error": str(exc)}
            await _save_history(
                alert_id,
                "github",
                "failed",
                error=str(exc)[:1000],
            )
            logger.exception("github_auto_issue_failed alert_id=%s", alert_id)

    return outcomes
