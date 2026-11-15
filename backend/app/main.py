from contextlib import asynccontextmanager
from pathlib import Path
import time

from backend.app.routes.analysis import (
    router as analysis_router,
)

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fastapi import FastAPI
from pymongo import ASCENDING, DESCENDING

from backend.app.routes.users import (
    router as users_router,
)

from backend.app.routes.auth import (
    router as auth_router,
)

from backend.app.routes.statistics import (
    router as statistics_router,
)

from backend.app.routes.dashboard import (
    router as dashboard_router,
)

from backend.app.database.connection import (
    client,
    database,
)

from backend.app.routes.events import router as events_router
from backend.app.routes.alerts import router as alerts_router
from backend.app.routes.integrations import (
    router as integrations_router,
)
from backend.app.observability import logger, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):

    await client.admin.command("ping")

    logger.info("MongoDB conectado correctamente")

    await database["events"].create_index(
        [
            ("user_id", ASCENDING),
            ("timestamp", DESCENDING),
        ]
    )

    await database["users"].create_index(
    "username",
    unique=True,
    )

    await database["alerts"].create_index(
        [
            ("user_id", ASCENDING),
            ("created_at", DESCENDING),
        ]
    )

    await database["sessions"].create_index(
        [
            ("username", ASCENDING),
            ("started_at", DESCENDING),
        ]
    )

    yield

    await client.close()


app = FastAPI(
    title="Detector de Anomalías NoSQL",
    description="API para monitoreo y detección de comportamientos anómalos.",
    version="0.1.0",
    lifespan=lifespan
)


@app.middleware("http")
async def telemetry_middleware(
    request,
    call_next,
):
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        latency = time.perf_counter() - started_at
        metrics.record(
            request.method,
            500,
            latency,
        )
        logger.exception(
            "request_error method=%s path=%s latency=%.6f",
            request.method,
            request.url.path,
            latency,
        )
        raise

    latency = time.perf_counter() - started_at

    metrics.record(
        request.method,
        response.status_code,
        latency,
    )

    logger.info(
        "request method=%s path=%s status=%s latency=%.6f",
        request.method,
        request.url.path,
        response.status_code,
        latency,
    )

    return response

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

FRONTEND_DIR = (
    PROJECT_ROOT
    / "frontend"
)


app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static",
)

app.include_router(analysis_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(statistics_router)
app.include_router(dashboard_router)
app.include_router(events_router)
app.include_router(alerts_router)
app.include_router(integrations_router)


@app.get(
    "/",
    include_in_schema=False,
)
async def login_page():

    return FileResponse(
        FRONTEND_DIR
        / "login.html"
    )

@app.get(
    "/dashboard",
    include_in_schema=False,
)
async def dashboard_page():

    return FileResponse(
        FRONTEND_DIR
        / "dashboard.html"
    )


@app.get("/health")
async def health_check():
    return {
        "status": "ok"
    }


@app.get("/metrics")
async def telemetry_metrics():
    return metrics.snapshot()


@app.get("/health/db")
async def database_health():

    await client.admin.command("ping")

    return {
        "status": "ok",
        "database": "connected"
    }

@app.get(
    "/events-page",
    include_in_schema=False,
)
async def events_page():

    return FileResponse(
        FRONTEND_DIR
        / "events.html"
    )

@app.get(
    "/alerts-page",
    include_in_schema=False,
)
async def alerts_page():

    return FileResponse(
        FRONTEND_DIR
        / "alerts.html"
    ) 

@app.get(
    "/statistics-page",
    include_in_schema=False,
)
async def statistics_page():

    return FileResponse(
        FRONTEND_DIR
        / "statistics.html"
    )

@app.get(
    "/activity-analysis",
    include_in_schema=False,
)
async def activity_analysis_page(): 

    return FileResponse(
        FRONTEND_DIR
        / "activity-analysis.html"
    )

@app.get(
    "/users-page",
    include_in_schema=False,
)
async def users_page():

    return FileResponse(
        FRONTEND_DIR
        / "users.html"
    )