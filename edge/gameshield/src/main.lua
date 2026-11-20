-- GameShield edge agent v0.1 (skeleton)
-- Flight recorder for economic events.
--
-- Design constraints (see docs/adr/0003-edge-protocol.md):
--   * no native binaries (managed hosts)
--   * never block the game loop
--   * local queue + async signed batch upload

local queue = {}

local function record(event)
    -- TODO phase 1: build event per schemas/economic-event.v1.schema.json
    queue[#queue + 1] = event
end

local function flush()
    -- TODO phase 1: sign batch (HMAC-SHA256) and POST to Config.IngestUrl
    -- Drop-oldest policy when Config.QueueMaxSize is exceeded.
end

-- TODO phase 1: hook economic events (money, items, vehicles, transfers)
-- via the server frameworks present in the target server.

CreateThread(function()
    while true do
        Wait(Config.FlushIntervalMs)
        if #queue > 0 then flush() end
    end
end)
