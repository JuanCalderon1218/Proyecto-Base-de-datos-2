# Detector de Anomalías NoSQL

## Documentación técnica del proyecto

**Sistema web inteligente para la detección y análisis de anomalías en operaciones de bases de datos NoSQL.**

Proyecto académico del curso **Base de Datos 2** de la Universidad Privada de Tacna.

## Objetivo

El sistema recibe eventos relacionados con operaciones NoSQL, los analiza mediante un motor de reglas y genera alertas cuando identifica comportamientos anómalos.

## Arquitectura general

```text
Simulador
   |
   | HTTP + X-API-Key
   v
FastAPI en Render
   |
   | Motor de detección
   v
MongoDB Atlas
   |
   v
Dashboard web
```

## Componentes principales

- **FastAPI:** backend y API REST.
- **MongoDB Atlas:** persistencia de usuarios, eventos y alertas.
- **Motor de detección:** aplica reglas de anomalías y calcula severidad.
- **Frontend:** dashboard, alertas, eventos, estadísticas y administración.
- **Simulador:** genera actividad normal y escenarios anómalos para pruebas.
- **Render:** plataforma de despliegue.
- **GitHub Actions:** genera y publica esta documentación.

## Seguridad

- **JWT:** autenticación de usuarios y control de acceso por roles.
- **X-API-Key:** protección del endpoint de recepción de eventos.
- Roles implementados: **admin** y **analyst**.

## Anomalías detectadas

1. Eliminación o actualización masiva.
2. Alta frecuencia de operaciones.
3. Fallos repetidos.
4. Operaciones en horario inusual.
5. Desviación respecto al comportamiento histórico.

## Documentación automática

La sección **Referencia técnica automática** se genera desde el código Python usando el módulo `ast`. El proceso extrae módulos, clases, atributos, métodos, funciones, parámetros y docstrings.

Cada cambio enviado a `main` vuelve a generar la referencia y publica el sitio mediante GitHub Pages.

## Documentos académicos

Los documentos de Visión, Factibilidad, SRS y SAD se encuentran en la carpeta `Documentacion/` del repositorio.
