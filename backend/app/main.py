from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.database.connection import client
from backend.app.routes.events import router as events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Comprobar conexión con MongoDB
    await client.admin.command("ping")
    print("MongoDB conectado correctamente")

    yield

    # Cerrar conexión al apagar FastAPI
    await client.close()


app = FastAPI(
    title="Detector de Anomalías NoSQL",
    description="API para monitoreo y detección de comportamientos anómalos.",
    version="0.1.0",
    lifespan=lifespan
)


app.include_router(events_router)


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