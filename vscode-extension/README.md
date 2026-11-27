# NoSQL Anomaly Monitor para Visual Studio Code

Extensión propia del proyecto **Sistema Web Inteligente para la Detección de Anomalías NoSQL**. Conecta VS Code con FastAPI/MongoDB y muestra el historial de eventos y alertas desde el editor; permite enviar pruebas controladas y consultar las integraciones automáticas de Discord/GitHub Issues.

## Funciones

- Panel integrado y botón propio en la barra lateral.
- Comprobar `/health` y cambiar el destino entre Render y localhost.
- Iniciar sesión por `POST /auth/login` (JWT), consultar `GET /dashboard/summary`, `/alerts`, `/events` e `/integrations/history`.
- Guardar `EVENT_API_KEY` y JWT mediante `vscode.SecretStorage` (no en el repositorio ni settings.json).
- Enviar eventos por `POST /events` con `X-API-Key`: normal, UPDATE de 550, DELETE de 550, DELETE de 1500, horario inusual y formulario personalizado.
- Mostrar resultado real de FastAPI: Score, severidad, reglas y estado de las integraciones.
- Abrir las incidencias de GitHub y el dashboard web.
- Confirmación antes de enviar eventos sintéticos. **No modifica documentos reales de MongoDB:** solo registra eventos en el detector, que pueden crear alertas y notificaciones.

## Instalación rápida

1. En VS Code: **Extensiones** (`Ctrl+Shift+X`) → menú `...` → **Install from VSIX...**.
2. Seleccionar `NoSQL_Anomaly_Monitor-1.0.0.vsix` y recargar VS Code si se solicita.
3. En la barra lateral abrir el icono **NoSQL Monitor** → **Abrir panel completo**.
4. Pulsa **Comprobar API**. La URL predeterminada es `https://detector-anomalias-nosql.onrender.com`.
5. Pulsa **API Key** e ingresa el `EVENT_API_KEY` de Render (no el JWT; no publicarlo).
6. Pulsa **Iniciar sesión** con las credenciales `admin` o `analyst` de tu aplicación. Es independiente de la API Key.
7. Pulsa **Actualizar** y prueba primero **Normal**. Después puedes enviar **DELETE 1500 · CRITICAL** (puede crear GitHub Issue/Discord).
8. Comprueba resultados en el panel y en GitHub/Discord. No repitas pruebas críticas sin necesidad.

## Prueba de desarrollo

Abre esta carpeta `vscode-extension` en VS Code, presiona `F5` para iniciar **Extension Development Host** y utiliza la barra lateral NoSQL Monitor. No requiere `npm install` para ejecutar; solo usa APIs nativas de VS Code.

Ejecuta `npm test` para las pruebas unitarias y `npm run check` para verificar sintaxis (requiere Node.js 18+ para la suite de tests).

## Empaquetado oficial

Con Node.js 22 o superior y conectividad al registro npm:

```bash
npm install -g @vscode/vsce
vsce package --no-dependencies
```

Si no tienes conexión al registro de npm, el ZIP de entrega incluye un instalador `.vsix` ensamblado directamente siguiendo la estructura VSIX; ejecuta el script `scripts/build_vsix.py` para regenerarlo.

## Publicación en el repositorio con pocos commits

El código fuente se mantiene en `vscode-extension/`, sin subir claves, tokens, `node_modules` ni instaladores `.vsix` al árbol fuente. Las pruebas de extremo a extremo se verificaron en VS Code con una operación READ normal y una operación DELETE simulada de 1500 registros, con Score 75, Discord enviado y GitHub Issue creada.

## Arquitectura

```text
VS Code (extensión JavaScript)
     ├── /health (GET, sin credenciales)
     ├── /auth/login (POST, usuario y contraseña)
     ├── /dashboard/summary, /alerts, /events, /integrations/history (GET, JWT)
     └── /events (POST, X-API-Key)
               └── FastAPI existente -> Motor de anomalías -> MongoDB Atlas
                                                   └── Discord / GitHub Issues
```

La extensión sirve como tercera integración del **entorno de desarrollo** si el docente acepta extensiones propias de VS Code. No sustituye las integraciones de alertas Discord/GitHub Issues ni implementa MCP/Agent Skills.
