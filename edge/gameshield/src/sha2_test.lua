-- Unit tests against official vectors. Run from edge/gameshield:
--   lua5.4 src/sha2_test.lua

local sha2 = require('src.sha2')

local function check(name, got, want)
    if got ~= want then
        error(('%s FAILED\n  got:  %s\n  want: %s'):format(name, got, want), 0)
    end
    print('ok  ' .. name)
end

-- FIPS 180-4
check('sha256("abc")',
    sha2.sha256_hex('abc'),
    'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')

check('sha256("")',
    sha2.sha256_hex(''),
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

check('sha256(2-block message)',
    sha2.sha256_hex('abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq'),
    '248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1')

-- RFC 4231
check('hmac-sha256 case 2 (Jefe)',
    sha2.hmac_sha256_hex('Jefe', 'what do ya want for nothing?'),
    '5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843')

check('hmac-sha256 case 1 (0x0b x20)',
    sha2.hmac_sha256_hex(string.rep('\11', 20), 'Hi There'),
    'b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7')

print('sha2_test: all vectors passed')
