# Zona horaria utilizada como referencia del sistema.
# UTC-5 corresponde, por ejemplo, a Perú.
BUSINESS_UTC_OFFSET = -5


# -----------------------------
# Alta frecuencia
# -----------------------------

HIGH_FREQUENCY_WINDOW_SECONDS = 60
HIGH_FREQUENCY_THRESHOLD = 100


# -----------------------------
# Fallos repetidos
# -----------------------------

FAILURE_WINDOW_MINUTES = 5
FAILURE_THRESHOLD = 5


# -----------------------------
# Horario inusual
# -----------------------------

UNUSUAL_HOUR_START = 0
UNUSUAL_HOUR_END = 6


# -----------------------------
# Comportamiento habitual
# -----------------------------

BEHAVIOR_MIN_SAMPLES = 20
BEHAVIOR_Z_THRESHOLD = 3.0


# -----------------------------
# Agrupación de alertas
# -----------------------------

ALERT_MERGE_MINUTES = 5