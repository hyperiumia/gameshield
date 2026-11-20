-- GameShield edge agent v0.2 — economic flight recorder
-- Design constraints (docs/adr/0003-edge-protocol.md):
--   * no native binaries (managed hosts)
--   * never block the game loop
--   * local queue + async HMAC-signed batch upload

local sha2 = require 'src.sha2'
local Queue = require 'src.queue'

math.randomseed(os.time() + GetGameTimer())

local Q = Queue.new(Config.QueueMaxSize)

local function api_key() return GetConvar(Config.ApiKeyConvar, '') end
local function secret() return GetConvar(Config.SecretConvar, '') end
local function server_id()
    local id = GetConvar(Config.ServerIdConvar, '')
    return id ~= '' and id or GetConvar('sv_hostname', 'unknown')
end

local function uuid_v4()
    local t = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
    return (t:gsub('[xy]', function(c)
        local v = (c == 'x') and math.random(0, 15) or math.random(8, 11)
        return string.format('%x', v)
    end))
end

local function iso_now()
    return os.date('!%Y-%m-%dT%H:%M:%SZ')
end

--- Record one economic event (schema: schemas/economic-event.v1.schema.json).
-- Usage from any server resource:
--   exports['gameshield']:record({
--     type = 'money.credit',
--     actor = { player_id = src, display_name = name, role = 'player' },
--     economy = { currency = 'USD', amount = 250000, balance_after = 320000 },
--     source = { resource = 'qb-core', event_name = 'player:paid' },
--   })
local function record(partial)
    if api_key() == '' or secret() == '' then
        return nil, 'gameshield not configured (set gameshield_api_key / gameshield_secret convars)'
    end
    if type(partial) ~= 'table' or type(partial.type) ~= 'string' then
        return nil, 'event requires a type'
    end

    local event = {
        schema_version = '1',
        event_id = partial.event_id or uuid_v4(),
        server_id = partial.server_id or server_id(),
        occurred_at = partial.occurred_at or iso_now(),
        type = partial.type,
        actor = partial.actor,
        economy = partial.economy,
        subject = partial.subject,
        source = partial.source or { resource = GetInvokingResource() or 'unknown' },
        context = partial.context,
    }

    Q:push(event)
    return event.event_id
end

local function flush()
    local batch = Q:pop_many(Config.MaxBatchSize)
    if #batch == 0 then return end

    local body = json.encode({ sent_at = iso_now(), events = batch })
    local ts = tostring(os.time())
    local sig = sha2.hmac_sha256_hex(secret(), ts .. '.' .. body)

    PerformHttpRequest(Config.IngestUrl, function(status)
        if status ~= 200 then
            for _, e in ipairs(batch) do
                Q:push(e) -- requeue; drop-oldest keeps memory bounded
            end
            print(('^1[gameshield]^7 ingest returned %s — batch requeued'):format(status))
        end
    end, 'POST', body, {
        ['Content-Type'] = 'application/json',
        ['X-GS-Key'] = api_key(),
        ['X-GS-Timestamp'] = ts,
        ['X-GS-Signature'] = sig,
    })
end

exports('record', record)

RegisterCommand('gs_flush', function()
    flush()
    print(('^2[gameshield]^7 flush requested — queue depth %d'):format(Q:count()))
end, true)

RegisterCommand('gs_status', function()
    print(('^2[gameshield]^7 server_id=%s queue=%d ingest=%s'):format(server_id(), Q:count(), Config.IngestUrl))
end, true)

CreateThread(function()
    while true do
        Wait(Config.FlushIntervalMs)
        if Q:count() > 0 then flush() end
    end
end)

print('^2[gameshield]^7 edge agent v0.2 loaded')
