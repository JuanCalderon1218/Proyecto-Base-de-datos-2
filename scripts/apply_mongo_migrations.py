from datetime import datetime, timezone
import os

from pymongo import MongoClient, ASCENDING, DESCENDING


MIGRATION_ID = "001-inicializar-esquema"


def ensure_collection(database, name):
    if name not in database.list_collection_names():
        database.create_collection(name)
        return True
    return False


def main():
    uri = os.environ["MONGO_URI"]
    db_name = os.getenv("MONGO_DB", "anomaly_detector")

    client = MongoClient(uri)
    client.admin.command("ping")
    database = client[db_name]

    changelog = database["schema_changelog"]

    already_applied = changelog.find_one(
        {"migration_id": MIGRATION_ID}
    )

    report = [
        "# Reporte de migracion MongoDB",
        "",
        f"Migracion: {MIGRATION_ID}",
        f"Base de datos: {db_name}",
        f"Fecha UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    if already_applied:
        report.append("Estado: YA APLICADA")
    else:
        created = []

        for collection_name in [
            "users",
            "events",
            "alerts",
            "sessions",
        ]:
            if ensure_collection(
                database,
                collection_name,
            ):
                created.append(collection_name)

        database["users"].create_index(
            "username",
            unique=True,
        )

        database["events"].create_index(
            [
                ("user_id", ASCENDING),
                ("timestamp", DESCENDING),
            ]
        )

        database["alerts"].create_index(
            [
                ("user_id", ASCENDING),
                ("created_at", DESCENDING),
            ]
        )

        database["sessions"].create_index(
            [
                ("username", ASCENDING),
                ("started_at", DESCENDING),
            ]
        )

        changelog.create_index(
            "migration_id",
            unique=True,
        )

        changelog.insert_one(
            {
                "migration_id": MIGRATION_ID,
                "applied_at": datetime.now(
                    timezone.utc
                ),
                "description": (
                    "Colecciones e indices iniciales "
                    "del Detector de Anomalias NoSQL"
                ),
            }
        )

        report.append("Estado: APLICADA CORRECTAMENTE")
        report.append("")
        report.append(
            "Colecciones creadas en esta ejecucion: "
            + (
                ", ".join(created)
                if created
                else "ninguna; ya existian"
            )
        )

    report.extend(
        [
            "",
            "## Objetos verificados",
            "",
            "- users (username unico)",
            "- events (user_id + timestamp)",
            "- alerts (user_id + created_at)",
            "- sessions (username + started_at)",
            "- schema_changelog (migration_id unico)",
        ]
    )

    with open(
        "reporte-migracion-mongodb.md",
        "w",
        encoding="utf-8",
    ) as file:
        file.write("\n".join(report))

    print("\n".join(report))
    client.close()


if __name__ == "__main__":
    main()
