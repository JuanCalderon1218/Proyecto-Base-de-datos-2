Sistema web inteligente para la detección de anomalías y comportamientos inusuales en bases de datos NoSQL
----------------------------------------------------------------------------------------------------------
Problema

Las bases de datos NoSQL, como MongoDB, permiten manejar grandes volúmenes de información y múltiples operaciones de forma flexible. Sin embargo, no todas las actividades anormales representan errores directos: un acceso en horario inusual, un incremento repentino de consultas, múltiples intentos fallidos de autenticación o una eliminación masiva pueden ser operaciones válidas individualmente, pero sospechosas al analizar su comportamiento en conjunto.

OWASP recomienda implementar mecanismos de monitoreo y generación de alertas ante patrones anómalos en bases de datos NoSQL. Asimismo, MongoDB incorpora herramientas de auditoría y monitoreo, pero estas se enfocan principalmente en registrar eventos, métricas y condiciones configuradas.

Por ello, el proyecto busca desarrollar una herramienta que no solo registre lo ocurrido, sino que analice los eventos y determine si el comportamiento observado se desvía de los patrones considerados normales, generando alertas para facilitar la supervisión del administrador.

Problema general:
¿Cómo detectar oportunamente anomalías y comportamientos inusuales en las operaciones realizadas sobre una base de datos NoSQL?

Objetivo general de investigación
->Analizar patrones de acceso y operaciones en bases de datos NoSQL para establecer criterios que permitan identificar automáticamente comportamientos anómalos.

Objetivos específicos de investigación
->Identificar al menos 5 tipos de anomalías relevantes en bases de datos NoSQL.
->Determinar las variables necesarias para su detección, como usuario, horario, frecuencia y tipo de operación.
->Construir un conjunto de pruebas con eventos normales y anómalos.
->Evaluar el mecanismo buscando una precisión mínima del 80 % en los escenarios definidos.

Objetivo general de la solución
->Desarrollar un sistema web inteligente para detectar anomalías y comportamientos inusuales en bases de datos NoSQL, inicialmente MongoDB, mediante el análisis de eventos y la generación de alertas.

Objetivos específicos de la solución
->Recopilar y almacenar eventos provenientes de MongoDB.
->Detectar como mínimo 5 categorías de comportamiento anómalo.
->Clasificar alertas en niveles bajo, medio y alto.
->Mostrar eventos y anomalías mediante un dashboard web.
->Permitir filtros por usuario, fecha, operación y severidad.
->Mantener un historial de anomalías para su posterior análisis.

Fuentes base
OWASP Foundation. NoSQL Security Cheat Sheet.
MongoDB. Auditing.
MongoDB Atlas. Monitoring and Alerts.
