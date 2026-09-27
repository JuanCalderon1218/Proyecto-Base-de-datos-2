import argparse
import os
import random
import time
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv


load_dotenv()

API_URL = os.getenv(
    "EVENT_API_URL",
    "http://127.0.0.1:8000/events",
)

EVENT_API_KEY = os.getenv(
    "EVENT_API_KEY",
    "",
)


USERS = [
    "usuario01",
    "usuario02",
    "usuario03",
    "usuario04",
    "usuario05",
]

COLLECTIONS = [
    "clientes",
    "ventas",
    "productos",
    "usuarios",
    "pedidos",
]

OPERATIONS = [
    "READ",
    "INSERT",
    "UPDATE",
    "DELETE",
]


def send_event(event: dict) -> None:
    """
    Envía un evento al backend.
    """

    try:
        response = httpx.post(
    	API_URL,
    	json=event,
    	headers={
        	"X-API-Key": EVENT_API_KEY,
    	},
    	timeout=5.0,
	)

        response.raise_for_status()

        saved_event = response.json()

        print(
            f"[OK] "
            f"{saved_event['event_id']} | "
            f"{saved_event['user_id']} | "
            f"{saved_event['operation']} | "
            f"{saved_event['records_affected']} registros | "
            f"success={saved_event['success']}"
        )

    except httpx.ConnectError:
        print(
            "[ERROR] No se pudo conectar con FastAPI. "
            "Verifica que el servidor esté ejecutándose."
        )

    except httpx.HTTPStatusError as error:
        print(
            f"[ERROR HTTP] "
            f"{error.response.status_code}: "
            f"{error.response.text}"
        )

    except Exception as error:
        print(f"[ERROR] {error}")

def simulate_behavior_deviation():
    print("\n--- DESVIACIÓN DE COMPORTAMIENTO ---\n")

    # Crear historial normal para usuario05
    for _ in range(25):
        event = {
            "user_id": "usuario05",
            "operation": "UPDATE",
            "collection": "productos",
            "records_affected": random.randint(5, 15),
            "success": True,
        }

        send_event(event)
        time.sleep(0.05)

    print("\n--- EVENTO ANÓMALO ---\n")

    anomalous_event = {
        "user_id": "usuario05",
        "operation": "UPDATE",
        "collection": "productos",
        "records_affected": 350,
        "success": True,
    }

    send_event(anomalous_event)

def generate_normal_event() -> dict:
    """
    Genera una operación considerada normal.
    """

    operation = random.choices(
        OPERATIONS,
        weights=[60, 15, 20, 5],
        k=1,
    )[0]

    if operation == "READ":
        records_affected = random.randint(1, 50)

    elif operation == "INSERT":
        records_affected = random.randint(1, 10)

    elif operation == "UPDATE":
        records_affected = random.randint(1, 30)

    else:
        records_affected = random.randint(1, 10)

    return {
        "user_id": random.choice(USERS),
        "operation": operation,
        "collection": random.choice(COLLECTIONS),
        "records_affected": records_affected,
        "success": True,
    }


def simulate_normal(count: int, delay: float) -> None:
    """
    Genera actividad normal.
    """

    print("\n--- SIMULACIÓN NORMAL ---\n")

    for _ in range(count):
        event = generate_normal_event()

        send_event(event)

        time.sleep(delay)


def simulate_mass_delete() -> None:
    """
    Simula una eliminación masiva.
    """

    print("\n--- ELIMINACIÓN MASIVA ---\n")

    event = {
        "user_id": "usuario01",
        "operation": "DELETE",
        "collection": "clientes",
        "records_affected": 1500,
        "success": True,
    }

    send_event(event)


def simulate_failures(count: int, delay: float) -> None:
    """
    Simula varias operaciones fallidas consecutivas.
    """

    print("\n--- FALLOS REPETIDOS ---\n")

    for _ in range(count):
        event = {
            "user_id": "usuario02",
            "operation": "UPDATE",
            "collection": "usuarios",
            "records_affected": 0,
            "success": False,
        }

        send_event(event)

        time.sleep(delay)


def simulate_high_frequency(count: int) -> None:
    """
    Genera muchas operaciones en poco tiempo.
    """

    print("\n--- ALTA FRECUENCIA ---\n")

    for _ in range(count):
        event = {
            "user_id": "usuario03",
            "operation": random.choice(
                ["READ", "UPDATE"]
            ),
            "collection": random.choice(
                COLLECTIONS
            ),
            "records_affected": random.randint(
                1,
                20,
            ),
            "success": True,
        }

        send_event(event)

        # Pausa muy pequeña para generar
        # muchas operaciones rápidamente.
        time.sleep(0.02)


def simulate_unusual_hour() -> None:
    """
    Simula una operación realizada a las
    2:30 AM en zona horaria UTC-5.
    """

    print("\n--- HORARIO INUSUAL ---\n")

    peru_timezone = timezone(
        timedelta(hours=-5)
    )

    now = datetime.now(peru_timezone)

    unusual_timestamp = now.replace(
        hour=2,
        minute=30,
        second=0,
        microsecond=0,
    )

    event = {
        "user_id": "usuario04",
        "operation": "UPDATE",
        "collection": "ventas",
        "records_affected": 25,
        "success": True,
        "timestamp": unusual_timestamp.isoformat(),
    }

    send_event(event)

def simulate_demo_normal_activity() -> None:
    """
    Genera actividad normal con una hora
    controlada para la demostracion.
    """

    peru_timezone = timezone(
        timedelta(hours=-5)
    )

    now = datetime.now(peru_timezone)

    normal_timestamp = now.replace(
        hour=14,
        minute=0,
        second=0,
        microsecond=0,
    )

    for _ in range(10):
        event = generate_normal_event()

        event["timestamp"] = (
            normal_timestamp.isoformat()
        )

        send_event(event)

        time.sleep(0.1)

def simulate_demo() -> None:
    """
    Ejecuta una demostracion completa
    de los principales escenarios.
    """

    print(
        "\n=============================="
        "\n DEMOSTRACION DEL SISTEMA"
        "\n==============================\n"
    )

    print(
    "\n[1/6] Actividad normal"
    )
    simulate_demo_normal_activity()

    print(
        "\n[2/6] Eliminacion masiva"
    )
    simulate_mass_delete()

    print(
        "\n[3/6] Fallos repetidos"
    )
    simulate_failures(
        count=5,
        delay=0.1,
    )

    print(
        "\n[4/6] Alta frecuencia"
    )
    simulate_high_frequency(
        count=110,
    )

    print(
        "\n[5/6] Horario inusual"
    )
    simulate_unusual_hour()

    print(
        "\n[6/6] Desviacion de comportamiento"
    )
    simulate_behavior_deviation()

    print(
        "\n=============================="
        "\n DEMOSTRACION FINALIZADA"
        "\n==============================\n"
    )

def main():
    
    parser = argparse.ArgumentParser(
        description=(
            "Simulador de eventos para "
            "el Detector de Anomalías NoSQL"
        )
        
    )

    parser.add_argument(
        "--mode",
        choices=[
    		"normal",
    		"mass-delete",
    		"failures",
    		"high-frequency",
    		"unusual-hour",
    		"behavior-deviation",
    		"demo",
	],
        default="normal",
        help="Tipo de simulación",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Cantidad de eventos",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Segundos entre eventos",
    )

    args = parser.parse_args()

    if args.mode == "normal":
        simulate_normal(
            count=args.count,
            delay=args.delay,
        )

    elif args.mode == "mass-delete":
        simulate_mass_delete()

    elif args.mode == "failures":
        simulate_failures(
            count=args.count,
            delay=args.delay,
        )

    elif args.mode == "high-frequency":
        simulate_high_frequency(
            count=args.count,
        )

    elif args.mode == "unusual-hour":
        simulate_unusual_hour()

    elif args.mode == "behavior-deviation":
        simulate_behavior_deviation()

    elif args.mode == "demo":
        simulate_demo()

if __name__ == "__main__":
    main()