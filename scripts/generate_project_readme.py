from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
REPORT = ROOT / "reporte-documentacion.md"

COLLECTIONS = {
    "users": [
        ("_id", "ObjectId", "Identificador interno de MongoDB"),
        ("username", "string", "Nombre de usuario único"),
        ("password_hash", "string", "Hash seguro de la contraseña"),
        ("role", "string", "Rol: admin o analyst"),
        ("active", "boolean", "Indica si el usuario está habilitado"),
        ("created_at", "datetime", "Fecha de creación"),
        ("created_by", "string", "Usuario administrador que creó el registro"),
        ("updated_at", "datetime", "Última actualización"),
        ("updated_by", "string", "Usuario que realizó la actualización"),
    ],
    "events": [
        ("_id", "ObjectId", "Identificador interno de MongoDB"),
        ("event_id", "string", "Identificador funcional EVT-XXXXXXXX"),
        ("user_id", "string", "Usuario asociado al evento"),
        ("operation", "string", "READ, INSERT, UPDATE o DELETE"),
        ("collection", "string", "Colección NoSQL afectada"),
        ("records_affected", "integer", "Cantidad de registros afectados"),
        ("success", "boolean", "Resultado de la operación"),
        ("timestamp", "datetime", "Fecha y hora del evento"),
        ("analyzed", "boolean", "Indica si el motor ya procesó el evento"),
        ("is_anomalous", "boolean", "Indica si se detectó anomalía"),
        ("anomaly_score", "integer", "Puntaje de anomalía de 0 a 100"),
        ("severity", "string/null", "low, medium, high, critical o null"),
        ("alert_id", "string/null", "Alerta relacionada si corresponde"),
    ],
    "alerts": [
        ("_id", "ObjectId", "Identificador interno de MongoDB"),
        ("alert_id", "string", "Identificador funcional ALT-XXXXXXXX"),
        ("event_id", "string", "Evento que originó la alerta"),
        ("latest_event_id", "string", "Último evento agrupado"),
        ("user_id", "string", "Usuario asociado"),
        ("operation", "string", "Operación relacionada"),
        ("collection", "string", "Colección relacionada"),
        ("records_affected", "integer", "Registros afectados"),
        ("types", "array", "Tipos de anomalía detectados"),
        ("signature", "string", "Firma utilizada para agrupar alertas"),
        ("score", "integer", "Puntaje de anomalía"),
        ("severity", "string", "low, medium, high o critical"),
        ("reasons", "array", "Razones de la detección"),
        ("detections", "array", "Detalle técnico de las reglas activadas"),
        ("status", "string", "pending, reviewed o resolved"),
        ("occurrence_count", "integer", "Cantidad de eventos agrupados"),
        ("event_timestamp", "datetime", "Fecha del evento"),
        ("created_at", "datetime", "Fecha de creación"),
        ("updated_at", "datetime", "Fecha de actualización"),
    ],
}


def parse_classes() -> list[tuple[str, list[str]]]:
    classes: list[tuple[str, list[str]]] = []
    schema_dir = ROOT / "backend" / "app" / "schemas"

    for path in sorted(schema_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue

            fields: list[str] = []

            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.append(item.target.id)

            classes.append((node.name, fields))

    return classes


def class_diagram() -> str:
    lines = ["classDiagram"]

    for class_name, fields in parse_classes():
        lines.append(f"    class {class_name} {{")
        for field in fields:
            lines.append(f"        +{field}")
        lines.append("    }")

    return "\n".join(lines)


def dictionary_markdown() -> str:
    lines: list[str] = []

    for collection, fields in COLLECTIONS.items():
        lines.extend([
            f"### Colección `{collection}`",
            "",
            "| Campo | Tipo | Descripción |",
            "|---|---|---|",
        ])

        for field, field_type, description in fields:
            lines.append(f"| `{field}` | {field_type} | {description} |")

        lines.append("")

    return "\n".join(lines)


def build_readme() -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""# Sistema web inteligente para la detección de anomalías en bases de datos NoSQL

> Proyecto académico de **Base de Datos 2 - Universidad Privada de Tacna**.

## Estado del proyecto

- Backend: FastAPI.
- Base de datos: MongoDB Atlas.
- Frontend: HTML, CSS y JavaScript.
- Despliegue: Render.
- Autenticación: JWT.
- Ingreso de eventos externos: X-API-Key.
- Documentación técnica: GitHub Pages.
- Backup: GitHub Actions.
- Release y despliegue: GitHub Actions + Render.

**Última generación automática del README:** {generated}

## Problemática

Las bases de datos NoSQL, como MongoDB, permiten manejar grandes volúmenes de información y múltiples operaciones de forma flexible. Sin embargo, no todas las actividades anormales representan errores directos: un acceso en horario inusual, un incremento repentino de consultas, múltiples operaciones fallidas o una eliminación masiva pueden ser válidas individualmente, pero sospechosas al analizar su comportamiento en conjunto.

El proyecto busca desarrollar una herramienta que no solo registre lo ocurrido, sino que analice los eventos y determine si el comportamiento observado se desvía de los patrones considerados normales, generando alertas que faciliten la supervisión.

### Problema general

**¿Cómo detectar oportunamente anomalías y comportamientos inusuales en las operaciones realizadas sobre una base de datos NoSQL?**

## Objetivos

### Objetivo general de investigación

Analizar patrones de acceso y operaciones en bases de datos NoSQL para establecer criterios que permitan identificar automáticamente comportamientos anómalos.

### Objetivos específicos de investigación

- Identificar al menos 5 tipos de anomalías relevantes en bases de datos NoSQL.
- Determinar variables necesarias para su detección, como usuario, horario, frecuencia y tipo de operación.
- Construir un conjunto de pruebas con eventos normales y anómalos.
- Evaluar el mecanismo buscando una precisión mínima del 80 % en los escenarios definidos.

### Objetivo general de la solución

Desarrollar un sistema web inteligente para detectar anomalías y comportamientos inusuales en bases de datos NoSQL, inicialmente MongoDB, mediante el análisis de eventos y la generación de alertas.

## Arquitectura general

```mermaid
flowchart LR
    SIM[Simulador de eventos] -->|HTTP + X-API-Key| API[FastAPI]
    WEB[Navegador] -->|JWT| API
    API --> DET[Motor de detección]
    DET --> DB[(MongoDB Atlas)]
    API --> DB
    API --> FRONT[Dashboard web]
```

## Estructura principal

```text
backend/
  app/
    auth/          Autenticación JWT y control de roles
    config/        Configuración del sistema
    database/      Conexión a MongoDB
    detection/     Motor y reglas de anomalías
    routes/        Endpoints REST
    schemas/       Modelos Pydantic
    services/      Servicios de alertas
frontend/          Dashboard y vistas web
simulator/         Generador de eventos de prueba
scripts/           Utilidades y automatizaciones
Documentacion/     Visión, Factibilidad, SRS y SAD
.github/workflows/ Automatizaciones GitHub Actions
```

## Diccionario de datos

MongoDB es una base documental y no aplica claves foráneas obligatorias como una base relacional. El siguiente diccionario representa la estructura utilizada por la aplicación.

{dictionary_markdown()}

## Diagrama lógico de entidades

Las relaciones son **lógicas**, basadas en los campos `user_id`, `event_id` y `alert_id`.

```mermaid
erDiagram
    USERS ||--o{{ EVENTS : "genera"
    USERS ||--o{{ ALERTS : "asociado a"
    EVENTS ||--o| ALERTS : "puede originar"

    USERS {{
        ObjectId _id
        string username
        string password_hash
        string role
        boolean active
        datetime created_at
    }}

    EVENTS {{
        ObjectId _id
        string event_id
        string user_id
        string operation
        string collection
        int records_affected
        boolean success
        datetime timestamp
        boolean is_anomalous
        int anomaly_score
        string severity
        string alert_id
    }}

    ALERTS {{
        ObjectId _id
        string alert_id
        string event_id
        string latest_event_id
        string user_id
        string severity
        int score
        string status
        int occurrence_count
        datetime created_at
    }}
```

## Diagrama de clases

Este diagrama se genera a partir de las clases definidas en `backend/app/schemas`.

```mermaid
{class_diagram()}
```

## Diagrama de componentes

```mermaid
flowchart TB
    UI[Frontend Web]
    AUTH[Autenticación y Roles]
    ROUTES[API Routes]
    DETECTION[Motor de Detección]
    ALERTS[Servicio de Alertas]
    DB[(MongoDB Atlas)]
    SIM[Simulador]

    UI --> ROUTES
    ROUTES --> AUTH
    SIM --> ROUTES
    ROUTES --> DETECTION
    DETECTION --> ALERTS
    ROUTES --> DB
    DETECTION --> DB
    ALERTS --> DB
```

## Diagrama de despliegue

```mermaid
flowchart LR
    USER[Usuario / Docente] -->|HTTPS| RENDER[Render Web Service]
    SIMPC[PC con simulador] -->|HTTPS + API Key| RENDER
    RENDER -->|TLS| ATLAS[(MongoDB Atlas)]

    GITHUB[GitHub Repository] --> ACTIONS[GitHub Actions]
    ACTIONS -->|Deploy Hook| RENDER
    ACTIONS -->|Backup seguro| ATLAS
    ACTIONS --> PAGES[GitHub Pages]
```

## Reglas de detección implementadas

| Regla | Condición principal | Resultado |
|---|---|---|
| Operación masiva | DELETE o UPDATE con gran cantidad de registros | Alerta por operación masiva |
| Horario inusual | Operaciones entre 00:00 y 05:59 | Incrementa el puntaje |
| Alta frecuencia | Muchas operaciones del mismo usuario en una ventana corta | Alerta por frecuencia |
| Fallos repetidos | Varias operaciones fallidas recientes | Alerta por fallos |
| Desviación de comportamiento | Valor significativamente diferente al histórico | Alerta estadística |

### Severidad

| Puntaje | Severidad |
|---:|---|
| 1-24 | low |
| 25-49 | medium |
| 50-74 | high |
| 75-100 | critical |

## Seguridad

### JWT

Se utiliza para autenticar a los usuarios de la aplicación. Los roles implementados son:

- `admin`: administración de usuarios y acceso al sistema.
- `analyst`: consulta y análisis de eventos y alertas.

### API Key

El endpoint `POST /events` valida el encabezado `X-API-Key` para evitar que clientes no autorizados inyecten eventos.

Los secretos reales no se almacenan en el repositorio. Se gestionan mediante variables de entorno y GitHub Secrets.

## Automatizaciones de GitHub

| Workflow | Objetivo |
|---|---|
| Documentación técnica - GitHub Pages | Genera y publica documentación técnica |
| Backup automático MongoDB | Genera copias de seguridad y un reporte como artifact |
| Release y despliegue Render | Crea releases y dispara el despliegue en Render |
| Documentación automática README | Regenera este README, diccionario y diagramas |

## Ejecución local

1. Crear y activar un entorno virtual.
2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Configurar un archivo `.env` a partir de `.env.example`.
4. Ejecutar:

```bash
uvicorn backend.app.main:app --reload
```

## Simulación

Ejemplo de demostración completa:

```bash
python simulator/simulator.py --mode demo
```

## Documentación académica

La carpeta `Documentacion/` contiene los documentos del proyecto:

- Visión.
- Factibilidad.
- SRS.
- SAD.

## Fuentes base

- OWASP Foundation - NoSQL Security Cheat Sheet.
- MongoDB - Auditing.
- MongoDB Atlas - Monitoring and Alerts.

---

Este README es actualizado mediante una automatización de GitHub Actions a partir de la estructura y documentación técnica del proyecto.
"""


def main() -> None:
    readme = build_readme()
    README.write_text(readme, encoding="utf-8")

    classes = parse_classes()
    report = [
        "# Reporte de generación de documentación",
        "",
        f"- Fecha UTC: {datetime.now(timezone.utc).isoformat()}",
        "- Estado: COMPLETADO",
        f"- Clases detectadas: {len(classes)}",
        f"- Colecciones documentadas: {len(COLLECTIONS)}",
        "- Diagramas generados: entidad lógica, clases, componentes y despliegue",
        "- Archivo actualizado: README.md",
    ]

    REPORT.write_text("\n".join(report), encoding="utf-8")
    print("README.md y reporte generados correctamente")


if __name__ == "__main__":
    main()
