output "key_value_id" {
  description = "ID del recurso Key Value gratuito creado por Terraform."
  value       = render_keyvalue.cache.id
}

output "internal_connection_string" {
  description = "Conexion interna del Key Value para servicios de la misma region."
  value       = render_keyvalue.cache.connection_info.internal_connection_string
  sensitive   = true
}
