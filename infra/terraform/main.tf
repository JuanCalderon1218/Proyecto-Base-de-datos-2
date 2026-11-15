resource "render_web_service" "detector" {
  name          = "detector-anomalias-nosql-terraform"
  plan          = "starter"
  region        = "oregon"
  start_command = "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"

  health_check_path = "/health"

  runtime_source = {
    native_runtime = {
      auto_deploy   = true
      branch        = "main"
      build_command = "pip install -r requirements.txt"
      repo_url      = "https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2"
      runtime       = "python"
    }
  }

  env_vars = {
    MONGO_URI = {
      value = var.mongo_uri
    }
    MONGO_DB = {
      value = var.mongo_db
    }
    SECRET_KEY = {
      value = var.secret_key
    }
    JWT_ALGORITHM = {
      value = "HS256"
    }
    ACCESS_TOKEN_EXPIRE_MINUTES = {
      value = "30"
    }
    EVENT_API_KEY = {
      value = var.event_api_key
    }
  }
}
