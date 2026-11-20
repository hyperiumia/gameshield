Config = {}

-- Ingest endpoint (cloud)
Config.IngestUrl = GetConvar('gameshield_ingest_url', 'http://127.0.0.1:8080/v1/events')

-- Secrets live in server convars, never hardcoded
Config.ApiKeyConvar = 'gameshield_api_key'
Config.SecretConvar = 'gameshield_secret'
Config.ServerIdConvar = 'gameshield_server_id'

-- Batch settings (never block the game loop)
Config.FlushIntervalMs = 5000
Config.MaxBatchSize = 200
Config.QueueMaxSize = 10000
