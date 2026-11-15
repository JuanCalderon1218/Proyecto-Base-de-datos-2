import httpx

from backend.app.config.settings import settings


def build_alert_text(alert: dict) -> str:
    return (
        f"Alerta {alert['alert_id']}\n"
        f"Usuario: {alert.get('user_id')}\n"
        f"Operacion: {alert.get('operation')}\n"
        f"Coleccion: {alert.get('collection')}\n"
        f"Score: {alert.get('score')}\n"
        f"Severidad: {alert.get('severity')}\n"
        f"Tipos: {', '.join(alert.get('types', []))}"
    )


async def create_github_issue(alert: dict) -> dict:
    if not settings.github_token:
        raise RuntimeError(
            "GITHUB_TOKEN no esta configurado"
        )

    url = (
        "https://api.github.com/repos/"
        f"{settings.github_repo}/issues"
    )

    payload = {
        "title": (
            f"[{alert.get('severity', 'unknown').upper()}] "
            f"Alerta {alert['alert_id']}"
        ),
        "body": build_alert_text(alert),
    }

    headers = {
        "Authorization": (
            f"Bearer {settings.github_token}"
        ),
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:
        response = await client.post(
            url,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    return {
        "provider": "github",
        "external_id": data.get("number"),
        "url": data.get("html_url"),
    }


async def send_discord_alert(
    alert: dict,
) -> dict:
    if not settings.discord_webhook_url:
        raise RuntimeError(
            "DISCORD_WEBHOOK_URL no esta configurado"
        )

    payload = {
        "content": (
            "**Detector de Anomalias NoSQL**\n"
            + build_alert_text(alert)
        )
    }

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:
        response = await client.post(
            settings.discord_webhook_url,
            json=payload,
        )
        response.raise_for_status()

    return {
        "provider": "discord",
        "status": "sent",
    }
