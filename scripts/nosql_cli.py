import argparse
import os
import sys

import httpx


API_URL = os.getenv(
    "DETECTOR_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

TOKEN = os.getenv(
    "DETECTOR_TOKEN",
    "",
)


def headers():
    if not TOKEN:
        return {}

    return {
        "Authorization": f"Bearer {TOKEN}"
    }


def request(
    method: str,
    path: str,
):
    response = httpx.request(
        method,
        f"{API_URL}{path}",
        headers=headers(),
        timeout=20.0,
    )

    if response.status_code >= 400:
        print(
            f"ERROR {response.status_code}: "
            f"{response.text}"
        )
        sys.exit(1)

    print(
        response.text
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "CLI del Detector de Anomalias NoSQL"
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser("health")
    subparsers.add_parser("metrics")
    subparsers.add_parser("alerts")
    subparsers.add_parser("events")
    subparsers.add_parser("sessions")

    args = parser.parse_args()

    routes = {
        "health": "/health",
        "metrics": "/metrics",
        "alerts": "/alerts",
        "events": "/events",
        "sessions": "/auth/sessions/me",
    }

    request(
        "GET",
        routes[args.command],
    )


if __name__ == "__main__":
    main()
