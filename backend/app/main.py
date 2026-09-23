from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymongo import ASCENDING, DESCENDING

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


@asynccontextmanager
async def lifespan(app: FastAPI):

    await client.admin.command("ping")

    print(
        "MongoDB conectado correctamente"
    )

    await database["events"].create_index(
        [
            ("user_id", ASCENDING),
            ("timestamp", DESCENDING),
        ]
    )

    await database["alerts"].create_index(
        [
            ("user_id", ASCENDING),
            ("created_at", DESCENDING),
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

app.include_router(statistics_router)
app.include_router(dashboard_router)
app.include_router(events_router)
app.include_router(alerts_router)


@app.get("/")
async def root():
    return {
        "message": "Detector de Anomalías NoSQL funcionando"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok"
    }


@app.get("/health/db")
async def database_health():

    await client.admin.command("ping")

    return {
        "status": "ok",
        "database": "connected"
    }