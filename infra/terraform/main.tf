resource "render_keyvalue" "cache" {
  name              = "detector-nosql-cache"
  plan              = "free"
  region            = "virginia"
  max_memory_policy = "allkeys_lru"
}
