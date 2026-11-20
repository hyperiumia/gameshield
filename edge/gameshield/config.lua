Config = {}

-- Ingest endpoint (cloud)
Config.IngestUrl = 'https://ingest.hyperiumia.dev/v1/events'

-- API key per server (set via server convar, never hardcode)
Config.ApiKeyConvar = 'gameshield_api_key'

-- Batch settings (never block the game loop)
Config.FlushIntervalMs = 5000
Config.MaxBatchSize = 200
Config.QueueMaxSize = 10000
