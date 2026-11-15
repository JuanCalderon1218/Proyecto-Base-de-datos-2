import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient


def main():
    uri = os.environ["MONGO_URI"]
    database_name = os.getenv("MONGO_DB", "anomaly_detector")
    output_path = Path(os.getenv("BACKUP_MANIFEST", "backup/source-manifest.json"))

    client = MongoClient(uri, serverSelectionTimeoutMS=20000)
    client.admin.command("ping")
    database = client[database_name]
    server_version = client.server_info().get("version", "desconocida")

    collections = {}
    total_documents = 0
    total_indexes = 0

    for collection_name in sorted(database.list_collection_names()):
        collection = database[collection_name]
        document_count = collection.count_documents({})
        indexes = []

        for index in collection.list_indexes():
            indexes.append({
                "name": index["name"],
                "keys": [[key, value] for key, value in index["key"].items()],
                "unique": bool(index.get("unique", False)),
            })

        collections[collection_name] = {
            "documents": document_count,
            "indexes": indexes,
        }
        total_documents += document_count
        total_indexes += len(indexes)

    manifest = {
        "database": database_name,
        "source_server_version": server_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_collections": len(collections),
        "total_documents": total_documents,
        "total_indexes": total_indexes,
        "collections": collections,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Base de datos: {database_name}")
    print(f"MongoDB Atlas: {server_version}")
    print(f"Colecciones inventariadas: {len(collections)}")
    print(f"Documentos inventariados: {total_documents}")
    print(f"Indices inventariados: {total_indexes}")
    print(f"Inventario generado: {output_path}")

    client.close()


if __name__ == "__main__":
    main()
