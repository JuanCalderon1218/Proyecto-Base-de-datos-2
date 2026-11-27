# Integraciones del Detector de Anomalías NoSQL

Esta página documenta el reto incorporado a la versión de noviembre de 2026. Las integraciones no sustituyen al motor de detección: **consumen el resultado del análisis** o permiten interactuar con la API existente.

## Comparación de las tres integraciones

| Integración | ¿Qué hace? | Forma de conexión |
|---|---|---|
| **Discord** | Notifica automáticamente cuando nace una alerta. | Webhook saliente desde FastAPI. |
| **GitHub Issues** | Abre incidencias automáticas solo para severidad HIGH/CRITICAL. | API de GitHub desde FastAPI. |
| **Visual Studio Code** | Permite consultar y registrar eventos de prueba directamente desde el editor. | Extensión propia (JavaScript) que consume la API REST con JWT o API Key. |

**GitHub Actions** es una herramienta adicional de automatización y CI/CD; no se presenta aquí como tercera integración de alertas.

## Ruta técnica de extremo a extremo

```text
Evento de MongoDB / agente   o   VS Code / simulador
                         |
                         v
              POST /events (X-API-Key)
                         |
                         v
            Motor de detección FastAPI
                         |
                Score + severidad
                         |
                  Nueva alerta
                         |
          +--------------+--------------+
          |                             |
          v                             v
  Discord webhook                GitHub Issues API
  (alertas nuevas)               (solo HIGH/CRITICAL)
          |                             |
          +-------------+---------------+
                        |
                        v
               integration_history
```

Cuando una detección se agrupa en una alerta equivalente pendiente, se evitan las notificaciones repetidas para la misma alerta. El historial registra `provider`, `status`, `result`, `error` y `executed_by`, cuando aplican.

## Integración 1: Discord

1. Configurar `DISCORD_WEBHOOK_URL` en las variables de entorno del backend.
2. Crear una nueva alerta mediante un evento detectado.
3. El backend envía usuario, operación, colección, Score, severidad y tipo de anomalía.
4. Consultar `integration_history` para comprobar `provider=discord` y `status=sent`.

## Integración 2: GitHub Issues

1. Configurar `GITHUB_TOKEN` y `GITHUB_REPO` en Render sin publicar sus valores.
2. Crear una alerta `high` o `critical`.
3. El backend crea un Issue con la información de la alerta.
4. Para `low` y `medium`, la integración GitHub queda como `skipped` en el historial.

Evidencia: [Issue #6 — ALT-ED529A2F (CRITICAL)](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/issues/6).

## Integración 3: Visual Studio Code

La extensión propia [NoSQL Anomaly Monitor](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/tree/main/vscode-extension) tiene un panel lateral con estadísticas, alertas, eventos, historial y formularios de prueba.

**Lecturas autenticadas:** `POST /auth/login` obtiene JWT y luego la extensión consulta `GET /dashboard/summary`, `GET /alerts`, `GET /events` y `GET /integrations/history`. **Escritura de pruebas:** `POST /events` con `X-API-Key`. La clave y el token se guardan en `vscode.SecretStorage`, no dentro del repositorio.

### Instalación

1. Instalar el archivo VSIX distribuido con el proyecto mediante **Extensiones → ... → Install from VSIX...**.
2. Abrir **NoSQL Monitor → Abrir panel completo**.
3. Configurar `https://detector-anomalias-nosql.onrender.com`.
4. Guardar la `EVENT_API_KEY` y usar **Iniciar sesión** con las credenciales del dashboard.
5. Actualizar la vista y ejecutar un evento normal antes de una prueba anómala.

El publicador registrado de Microsoft Marketplace es `calderonmango`. Para instalar desde la búsqueda pública, comprobar primero que la publicación haya terminado su verificación en el Marketplace.

## Pruebas ejecutadas

| Escenario | Resultado observado |
|---|---|
| READ sintético de 3 registros enviado desde VS Code | `EVT-2C5BF461`, Score 0, NORMAL, sin alerta. |
| DELETE sintético de 1 500 registros desde VS Code | `EVT-7F5D97E3`, `MASS_DELETE`, Score 75, CRITICAL. |
| Integraciones de la prueba CRITICAL | Discord `sent`; GitHub `created`; alerta `ALT-ED529A2F`; Issue #6. |
| UPDATE real de 550 documentos desde Atlas | `MASS_UPDATE`, Score 40, MEDIUM; Discord notificado. |
| DELETE real de 550 documentos desde Atlas | `MASS_DELETE`, Score 50, HIGH; Discord e incidencia GitHub. |

Los eventos enviados desde la extensión son **sintéticos**, por lo tanto **no eliminan documentos reales**. Los eventos captados desde Atlas por el agente sí corresponden a modificaciones reales del lote de pruebas.

## Limitaciones y siguientes pasos

- El agente Change Streams requiere estar activo; actualmente se ejecuta desde la PC de prueba. No es un servicio permanente en la nube.
- MongoDB Change Streams no registra lecturas ni fallos de aplicación: esas acciones requieren instrumentación o simulación.
- Las notificaciones pueden crear mensajes e incidencias reales, incluso cuando el evento de origen es simulado. No repetir pruebas críticas innecesariamente.
- La disponibilidad pública de la extensión depende de la validación del Microsoft Marketplace, independiente de que funcione localmente.

## Referencias

- [Código y guía de la extensión](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/tree/main/vscode-extension)
- [Servicio de integración automática](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/blob/main/backend/app/services/alert_integrations.py)
- [Anexo FD05 del reto](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/blob/main/Documentacion/FD05_Anexo_Integraciones_CALDERON_MANGO_2026.md)
