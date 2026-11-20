-- SHA-256 + HMAC-SHA256, pure Lua 5.4 (FiveM server runtime has no crypto lib).
-- Verified against FIPS 180-4 / RFC 4231 vectors in sha2_test.lua.

local M = {}

local K = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
}

local function u32(n)
    return n & 0xFFFFFFFF
end

local function rotr(x, n)
    x = u32(x)
    return u32((x >> n) | ((x << (32 - n)) & 0xFFFFFFFF))
end

local function to_hex(s)
    return (s:gsub('.', function(c)
        return string.format('%02x', string.byte(c))
    end))
end

local function be32(n)
    return string.char((n >> 24) & 0xFF, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF)
end

local function digest_raw(msg)
    local h = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
    }

    local len = #msg
    local bitlen_hi = math.floor((len * 8) / 4294967296)
    local bitlen_lo = u32(len * 8)

    msg = msg .. '\128'
    while (#msg % 64) ~= 56 do
        msg = msg .. '\0'
    end
    msg = msg .. be32(bitlen_hi) .. be32(bitlen_lo)

    for i = 1, #msg, 64 do
        local w = {}
        for t = 0, 15 do
            local j = i + t * 4
            w[t] = u32(
                (msg:byte(j) << 24) |
                (msg:byte(j + 1) << 16) |
                (msg:byte(j + 2) << 8) |
                msg:byte(j + 3)
            )
        end
        for t = 16, 63 do
            local w15, w2 = w[t - 15], w[t - 2]
            local s0 = u32(rotr(w15, 7) ~ rotr(w15, 18) ~ (w15 >> 3))
            local s1 = u32(rotr(w2, 17) ~ rotr(w2, 19) ~ (w2 >> 10))
            w[t] = u32(w[t - 16] + s0 + w[t - 7] + s1)
        end

        local a, b, c, d, e, f, g, hh = h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8]
        for t = 0, 63 do
            local S1 = u32(rotr(e, 6) ~ rotr(e, 11) ~ rotr(e, 25))
            local ch = u32((e & f) ~ ((~e) & g))
            local t1 = u32(hh + S1 + ch + K[t + 1] + w[t])
            local S0 = u32(rotr(a, 2) ~ rotr(a, 13) ~ rotr(a, 22))
            local maj = u32((a & b) ~ (a & c) ~ (b & c))
            local t2 = u32(S0 + maj)
            hh = g
            g = f
            f = e
            e = u32(d + t1)
            d = c
            c = b
            b = a
            a = u32(t1 + t2)
        end

        h[1] = u32(h[1] + a)
        h[2] = u32(h[2] + b)
        h[3] = u32(h[3] + c)
        h[4] = u32(h[4] + d)
        h[5] = u32(h[5] + e)
        h[6] = u32(h[6] + f)
        h[7] = u32(h[7] + g)
        h[8] = u32(h[8] + hh)
    end

    local out = {}
    for i = 1, 8 do
        out[i] = be32(h[i])
    end
    return table.concat(out)
end

function M.sha256_hex(msg)
    return to_hex(digest_raw(msg))
end

function M.hmac_sha256_hex(key, msg)
    if #key > 64 then
        key = digest_raw(key)
    end
    if #key < 64 then
        key = key .. string.rep('\0', 64 - #key)
    end

    local o_pad, i_pad = {}, {}
    for i = 1, 64 do
        local kb = key:byte(i)
        o_pad[i] = string.char(kb ~ 0x5c)
        i_pad[i] = string.char(kb ~ 0x36)
    end

    local inner = digest_raw(table.concat(i_pad) .. msg)
    return to_hex(digest_raw(table.concat(o_pad) .. inner))
end

return M
