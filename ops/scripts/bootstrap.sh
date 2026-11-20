#!/usr/bin/env bash
set -euo pipefail

echo "==> Hyperium IA · bootstrap"

sudo apt-get update
sudo apt-get install -y build-essential pkg-config libssl-dev

git curl jq unzip make ca-certificates

if ! command -v cargo >/dev/null 2>&1; then
curl --proto '=https' --tlsv1.2 -sSf 
https://sh.rustup.rs
 | sh -s -- -y
source "$HOME/.cargo/env"
fi

if ! command -v uv >/dev/null 2>&1; then
curl -LsSf 
https://astral.sh/uv/install.sh
 | sh
fi

if [ ! -s "
H
O
M
E
/
.
n
v
m
/
n
v
m
.
s
h
"
]
;
t
h
e
n
c
u
r
l
−
o
−
h
t
t
p
s
:
/
/
r
a
w
.
g
i
t
h
u
b
u
s
e
r
c
o
n
t
e
n
t
.
c
o
m
/
n
v
m
−
s
h
/
n
v
m
/
v
0.40.1
/
i
n
s
t
a
l
l
.
s
h
∣
b
a
s
h
f
i
s
o
u
r
c
e
"
HOME/.nvm/nvm.sh"];thencurl−o−https://raw.githubusercontent.com/nvm−sh/nvm/v0.40.1/install.sh∣bashfisource"HOME/.nvm/nvm.sh"
nvm install --lts

if ! command -v docker >/dev/null 2>&1; then
sudo apt-get install -y docker.io docker-compose-v2
sudo usermod -aG docker "$USER"
fi

echo "==> Toolchain versions:"
cargo --version || true
uv --version || true
node --version || true
docker --version || true
echo "==> Bootstrap complete."
