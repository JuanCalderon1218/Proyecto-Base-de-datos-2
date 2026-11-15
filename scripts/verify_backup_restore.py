import json
import os
import sys
from pathlib import Path

from pymongo import MongoClient


def index_signature(index):
    return (
        index["name"],
        tuple((key, value) for key, value in index["key"].items()),
        bool(index.get("unique", False)),
    )


def main():
    manifest_path = Path(
        os.getenv("BACKUP_MANIFEST", "backup/source-manifest.json")
    )
    report_path = Path(
        os.getenv("RESTORE_REPORT", "backup/restore-verification.md")
    )
    local_uri = os.getenv("LOCAL_MONGO_URI", "mongodb://127.0.0.1:27017")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    database_name = manifest["database"]

    client = MongoClient(local_uri, serverSelectionTimeoutMS=20000)
    client.admin.command("ping")
    database = client[database_name]

    expected_collections = set(manifest["collections"])
    actual_collections = set(database.list_collection_names())

    failures = []
    rows = []
    restored_documents = 0
    restored_indexes = 0

    missing_collections = expected_collections - actual_collections
    extra_collections = actual_collections - expected_collections

    for name in sorted(missing_collections):
        failures.append(f"No se restauro la coleccion {name}.")

    for name in sorted(extra_collections):
        failures.append(f"Se encontro una coleccion inesperada {name}.")

    for collection_name, expected in sorted(manifest["collections"].items()):
        if collection_name not in actual_collections:
            continue

        collection = database[collection_name]
        actual_documents = collection.count_documents({})
        expected_documents = expected["documents"]
        restored_documents += actual_documents

        actual_indexes = list(collection.list_indexes())
        expected_signatures = {
            (
                item["name"],
                tuple((key, value) for key, value in item["keys"]),
                item["unique"],
            )
            for item in expected["indexes"]
        }
        actual_signatures = {
            index_signature(item)
            for item in actual_indexes
        }
        restored_indexes += len(actual_indexes)

        if actual_documents != expected_documents:
            failures.append(
                f"{collection_name}: documentos esperados "
                f"{expected_documents}, restaurados {actual_documents}."
            )

        missing_indexes = expected_signatures - actual_signatures
        if missing_indexes:
            failures.append(
                f"{collection_name}: faltan indices "
                f"{sorted(missing_indexes, key=str)}."
            )

        rows.append(
            f"| {collection_name} | {expected_documents} | "
            f"{actual_documents} | {len(expected_signatures)} | "
            f"{len(actual_signatures)} | "
            f"{'OK' if actual_documents == expected_documents and not missing_indexes else 'ERROR'} |"
        )

    result = "SUPERADO" if not failures else "FALLIDO"
    report = [
        "# Verificacion de restauracion MongoDB",
        "",
        f"- Base de datos: {database_name}",
        f"- Version de origen: {manifest.get('source_server_version', 'No registrada')}",
        f"- Fecha del inventario: {manifest.get('generated_at', 'No registrada')}",
        f"- Colecciones de origen: {len(expected_collections)}",
        f"- Colecciones restauradas: {len(actual_collections)}",
        f"- Documentos restaurados: {restored_documents}",
        f"- Indices inspeccionados en destino: {restored_indexes}",
        "",
        "| Coleccion | Documentos origen | Documentos restaurados | Indices origen | Indices destino | Resultado |",
        "|---|---:|---:|---:|---:|---|",
        *rows,
        "",
        f"## Resultado: {result}",
        "",
    ]

    if failures:
        report.extend(["## Incidencias", ""])
        report.extend(f"- {failure}" for failure in failures)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))

    client.close()

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
