# Infraestructura Terraform

Esta configuracion utiliza el proveedor oficial de Render para describir
un servicio web FastAPI como infraestructura como codigo.

## Seguridad

Los secretos no se guardan en Git. Terraform recibe:

- RENDER_API_KEY
- RENDER_OWNER_ID
- TF_VAR_mongo_uri
- TF_VAR_secret_key
- TF_VAR_event_api_key

desde GitHub Secrets.

## Importante sobre costos

El recurso render_web_service del proveedor Terraform no ofrece el plan Free.
La configuracion usa Starter y por eso el apply esta deshabilitado por defecto.

El workflow siempre ejecuta fmt, init y validate. El apply solo se ejecuta
manualmente cuando el usuario marca apply_infrastructure=true.
