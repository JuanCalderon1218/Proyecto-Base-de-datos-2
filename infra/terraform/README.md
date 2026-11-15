# Infraestructura Terraform

Esta configuracion utiliza el proveedor oficial de Render para crear un recurso
Render Key Value gratuito, compatible con Redis, como infraestructura de apoyo
para el Detector de Anomalias NoSQL.

## Recurso administrado

- Nombre: detector-nosql-cache
- Tipo: Render Key Value
- Plan: free
- Region: virginia
- Politica de memoria: allkeys_lru
- Costo base estimado: USD 0/mes

El recurso Free tiene limites de memoria y es volatil: su contenido puede perderse
cuando Render reinicia o mantiene el servicio. Por ello debe utilizarse como cache,
nunca como almacenamiento persistente.

La aplicacion web principal permanece en su servicio Render Free existente.
Este Terraform no crea un segundo Web Service ni cambia su plan.

## Seguridad

Los secretos no se guardan en Git. Terraform recibe:

- RENDER_API_KEY
- RENDER_OWNER_ID

desde GitHub Secrets.

La cadena interna de conexion se expone como output sensible y no debe publicarse.

## Ejecucion

El workflow siempre ejecuta fmt, init y validate y genera reportes.
La creacion real del recurso solo se ejecuta manualmente al marcar
apply_infrastructure=true.
