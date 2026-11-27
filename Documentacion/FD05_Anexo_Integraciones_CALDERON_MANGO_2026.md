# Anexo del informe final FD05: Integraciones externas y validación funcional

**Proyecto:** Sistema Web Inteligente para la Detección de Anomalías en Bases de Datos NoSQL  
**Curso:** Base de Datos II — Universidad Privada de Tacna  
**Docente:** Ing. Patrick José Cuadros Quiroga  
**Integrantes:** Juan Carlos Calderon Rodriguez; Franco Mango Puma  
**Actualización:** noviembre de 2026  
**Carácter:** anexo complementario del [FD05 original](FD05_Informe_Final_Detector_Anomalias_NoSQL_CALDERON_MANGO.pdf), que se conserva sin modificaciones.

## 1. Propósito de la ampliación

Documentar las integraciones implementadas después de la versión inicial del informe final y registrar las evidencias del reto de interoperabilidad del sistema. El backend y sus cinco reglas de detección siguen siendo los componentes que determinan el carácter anómalo del evento.

## 2. Solución integrada

Se incorporaron dos integraciones automáticas de gestión de alertas y una extensión propia de entorno de desarrollo:

**Discord.** Al generarse una alerta nueva, el backend envía la notificación al webhook configurado. Incluye datos de usuario, operación, colección, puntuación, severidad y reglas activadas. Se registra el resultado en la colección `integration_history`.

**GitHub Issues.** Si una alerta nueva alcanza severidad `high` o `critical`, la API de GitHub permite registrar automáticamente una incidencia para seguimiento técnico. Para severidades inferiores, el servicio omite la creación y deja constancia del resultado.

**Visual Studio Code.** Se desarrolló la extensión propia **NoSQL Anomaly Monitor**, versión 1.0.0, identificada por el publicador `calderonmango`. El panel integrado consulta información mediante endpoints autenticados JWT, permite enviar eventos de prueba con `X-API-Key`, representa Score y severidad y facilita el acceso a GitHub Issues. Su código fuente, pruebas e instrucciones están en `vscode-extension/`.

GitHub Actions continúa siendo la herramienta de integración continua, documentación, respaldos y despliegue; no debe confundirse con una tercera integración automática de alertas.

## 3. Flujo funcional

1. El sistema recibe un evento desde el agente de MongoDB, el simulador o la extensión VS Code.
2. FastAPI valida los datos y registra el evento en MongoDB.
3. El motor aplica las cinco reglas, suma las puntuaciones activadas y asigna severidad.
4. Una anomalía produce una alerta nueva o se agrupa con una existente.
5. Si la alerta es nueva, se intentan las integraciones de Discord y GitHub según las reglas de severidad.
6. Los resultados se conservan en `integration_history` y se consultan desde el dashboard o la extensión.

## 4. Evidencias de aceptación

| Caso | Evidencia |
|---|---|
| Evento normal desde VS Code | `EVT-2C5BF461`, READ, Score 0, sin anomalía. |
| Anomalía crítica desde VS Code | `EVT-7F5D97E3`, DELETE sintético de 1 500 registros, Score 75 y `CRITICAL`. |
| Alerta y notificaciones | `ALT-ED529A2F`, Discord `sent`, GitHub `created`. |
| Incidencia verificable | [GitHub Issue #6](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/issues/6), `[CRITICAL] Alerta ALT-ED529A2F`. |
| Pruebas directas de MongoDB Atlas | UPDATE de 550 registros: MEDIUM (40); DELETE de 550: HIGH (50), con notificaciones comprobadas. |

**Alcance de la evidencia:** el evento DELETE de 1 500 registros generado desde VS Code fue sintético y **no borró documentos reales**. En cambio, la prueba desde Data Explorer actuó sobre los documentos etiquetados del lote de demostración. La interfaz mostró respuestas del backend e historial de integraciones; la validación publicada de Marketplace depende de la revisión externa de Microsoft.

## 5. Seguridad y restricciones

- El panel usa credenciales de usuario y JWT para consultar las rutas protegidas.
- Los envíos de prueba utilizan una API Key específica en el encabezado `X-API-Key`.
- La extensión almacena credenciales mediante el almacén seguro de VS Code (`SecretStorage`); no se incluyen secretos en el repositorio.
- El agente Change Streams que observa cambios reales se ejecuta separadamente y necesita permanecer activo. No puede observar lecturas ni errores de aplicación sin instrumentación adicional.
- Los servicios externos pueden fallar sin invalidar el registro de la anomalía; su resultado se guarda cuando es posible en `integration_history`.

## 6. Resultado y trabajo futuro

Las pruebas permitieron comprobar la comunicación **VS Code → FastAPI → motor → MongoDB → Discord/GitHub** y el monitoreo de cambios reales desde Atlas mediante un agente separado. Como mejora futura se plantea hospedar el agente en un servicio permanente y extender la instrumentación a operaciones READ y fallos reales. La publicación pública de la extensión debe verificarse por separado en el Marketplace.

## 7. Repositorios y consulta

- [Código del sistema](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2)
- [Código y manual de la extensión](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/tree/main/vscode-extension)
- [Portal de integraciones](https://juancalderon1218.github.io/Proyecto-Base-de-datos-2/integraciones/)
- [Incidencias automáticas del detector](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/issues)
