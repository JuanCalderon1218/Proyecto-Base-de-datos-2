# Detector de Anomalías NoSQL

**Sistema web inteligente para detectar comportamientos inusuales en operaciones de bases de datos NoSQL.**

Proyecto académico de Base de Datos II de la **Universidad Privada de Tacna**. Equipo: **Juan Carlos Calderon Rodriguez y Franco Mango Puma**.

## ¿Qué hace el sistema?

El sistema recibe eventos de operaciones, aplica **cinco reglas** de detección y calcula un **Score entre 0 y 100**, clasificado como LOW, MEDIUM, HIGH o CRITICAL. Los eventos, las alertas y el historial de integraciones se almacenan en **MongoDB Atlas**.

## Arquitectura actual

```text
MongoDB Atlas (base monitoreada)  -- Change Streams --> Agente Python local
                                                             |
Simulador o extensión de VS Code -- POST /events ------------+--> FastAPI (Render)
                                                                   |
                                                          Motor de detección
                                                                   |
                                            MongoDB Atlas: events / alerts / history
                                                                   |
                                         Discord (alertas nuevas) / GitHub Issues (HIGH+)
```

La aplicación web y el backend se encuentran en Render. **El agente local es un proceso separado:** debe permanecer ejecutándose para observar cambios reales. Change Streams informa sobre INSERT, UPDATE y DELETE; READ y operaciones fallidas requieren instrumentación o eventos de prueba.

## Componentes principales

| Componente | Función |
|---|---|
| **FastAPI** | Recepción, análisis y consulta mediante API REST. |
| **Motor de detección** | Cinco reglas y cálculo de Score/severidad. |
| **MongoDB Atlas** | Persistencia de usuarios, eventos, alertas e historial. |
| **Dashboard web** | Consulta y seguimiento de anomalías. |
| **Agente Python** | Observa cambios reales mediante MongoDB Change Streams. |
| **Discord** | Notifica cuando se crea una alerta nueva. |
| **GitHub Issues** | Registra incidencias automáticas para HIGH o CRITICAL. |
| **NoSQL Anomaly Monitor** | Extensión VS Code para consultar y enviar eventos de prueba a la API. |
| **GitHub Actions** | Respaldo, validación, documentación y despliegue. |

## Seguridad

Autenticación **JWT** para los usuarios de la aplicación (roles admin y analyst), y encabezado **X-API-Key** para `POST /events`. Las claves reales no deben publicarse. La extensión almacena sus secretos mediante **VS Code SecretStorage**.

## Anomalías detectadas

1. Operaciones masivas (UPDATE / DELETE).
2. Alta frecuencia de operaciones.
3. Fallos repetidos.
4. Actividad en horario inusual.
5. Desviación respecto al comportamiento histórico.

## Reto de integraciones y demostración

Se implementaron **Discord** y **GitHub Issues** como integraciones automáticas del backend. Además, la extensión propia para **Visual Studio Code** se conecta a FastAPI para mostrar eventos, alertas, el Score y su historial; también envía eventos controlados.

En una prueba observada, la extensión generó un evento DELETE **sintético** de 1 500 registros: `MASS_DELETE`, Score **75**, severidad **CRITICAL**, con envío a Discord y creación de [GitHub Issue #6](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/issues/6). **El evento simulado no borra documentos reales**.

Consulta la [guía de integraciones](integraciones.md) para la arquitectura, las pruebas y la distinción entre monitoreo real y simulación.

## Enlaces del proyecto

- [Repositorio completo](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2)
- [Extensión y guía de instalación de VS Code](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/tree/main/vscode-extension)
- [Aplicación web en Render](https://detector-anomalias-nosql.onrender.com)
- [API Swagger](https://detector-anomalias-nosql.onrender.com/docs)
- [Documentación académica e informe final FD05](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/tree/main/Documentacion)
- [Anexo FD05 del reto de integraciones](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/blob/main/Documentacion/FD05_Anexo_Integraciones_CALDERON_MANGO_2026.md)
- [GitHub Issues](https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/issues)

## Documentación automática

La referencia técnica se genera automáticamente desde el código Python mediante `ast` y se publica con GitHub Pages. Este apartado introductorio y la [guía de integraciones](integraciones.md) se mantienen en `docs/`.
