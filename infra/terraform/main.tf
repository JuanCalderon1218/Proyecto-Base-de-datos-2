resource "render_keyvalue" "cache" {
  name              = "laboratorio03-bd2-redis"
  plan              = "free"
  region            = "virginia"
  max_memory_policy = "allkeys_lru"
  persistence_mode  = "off"

  ip_allow_list = [
    {
      cidr_block  = "0.0.0.0/0"
      description = "GitHub Actions - Laboratorio 03"
    }
  ]
}
