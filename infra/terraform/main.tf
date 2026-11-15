resource "render_keyvalue" "cache" {
  name              = "laboratorio03-bd2-redis"
  plan              = "free"
  region            = "virginia"
  max_memory_policy = "allkeys_lru"
  persistence_mode  = "off"
}
