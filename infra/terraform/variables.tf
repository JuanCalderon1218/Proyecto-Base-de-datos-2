variable "mongo_uri" {
  description = "Cadena de conexion de MongoDB Atlas"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Clave de firma JWT"
  type        = string
  sensitive   = true
}

variable "event_api_key" {
  description = "API Key para la ingesta de eventos"
  type        = string
  sensitive   = true
}

variable "mongo_db" {
  description = "Nombre de la base de datos"
  type        = string
  default     = "anomaly_detector"
}
