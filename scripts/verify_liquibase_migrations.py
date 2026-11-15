import os
import sys

from pymongo import MongoClient


EXPECTED_INDEXES = {
    "users": [
        ({"username": 1}, True),
    ],
    "events": [
        ({"user_id": 1, "timestamp": -1}, False),
    ],
    "alerts": [
        ({"user_id": 1, "created_at": -1}, False),
    ],
    "sessions": [
        ({"username": 1, "started_at": -1}, False),
    ],
    "integration_history": [
        ({"alert_id": 1, "created_at": -1}, False),
    ],
}


def normalize_keys(index):
    return dict(index["key"].items())


def main():
    uri = os.environ["MONGO_URI"]
    database_name = os.getenv("MONGO_DB", "anomaly_detector")

    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    client.admin.command("ping")
    database = client[database_name]

    failures = []
    report = [
        "# Verificacion de migraciones Liquibase",
        "",
        f"Base de datos: {database_name}",
        "",
    ]

    existing_collections = set(database.list_collection_names())

    for collection_name, expected_indexes in EXPECTED_INDEXES.items():
        if collection_name not in existing_collections:
            failures.append(f"No existe la coleccion {collection_name}")
            report.append(f"- {collection_name}: NO EXISTE")
            continue

        actual_indexes = list(database[collection_name].list_indexes())

        for expected_keys, expected_unique in expected_indexes:
            match = next(
                (
                    index
                    for index in actual_indexes
                    if normalize_keys(index) == expected_keys
                ),
                None,
            )

            if match is None:
                failures.append(
                    f"Falta indice en {collection_name}: {expected_keys}"
                )
                report.append(
                    f"- {collection_name} {expected_keys}: FALTA"
                )
                continue

            actual_unique = bool(match.get("unique", False))
            if actual_unique != expected_unique:
                failures.append(
                    f"Propiedad unique incorrecta en {collection_name}: "
                    f"{expected_keys}"
                )
                report.append(
                    f"- {collection_name} {expected_keys}: "
                    f"UNIQUE INCORRECTO"
                )
                continue

            report.append(
                f"- {collection_name} {expected_keys}: OK "
                f"(unique={actual_unique})"
            )

    client.close()

    if failures:
        report.extend(["", "## Errores", ""])
        report.extend(f"- {failure}" for failure in failures)
        result = "FALLIDO"
    else:
        result = "SUPERADO"

    report.extend(["", f"Resultado: {result}"])
    output = "\n".join(report)

    with open("liquibase-verification.md", "w", encoding="utf-8") as file:
        file.write(output)

    print(output)

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
