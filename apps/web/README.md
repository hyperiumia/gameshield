# apps/web — GameShield Dashboard

Panel de integridad economica para owners de servidores: timeline,
alertas explicables y exportacion de evidencia.

## Desarrollo

    npm install
    npm run dev

Abre http://localhost:5173 — proxy de /v1 hacia engine (:8000).

Variables (archivo .env local, opcional):

    VITE_API_BASE=https://api.tu-dominio

Si VITE_API_BASE esta vacio se usa el mismo origen (proxy de desarrollo).

## Modo demo (ventas sin backend)

Boton "Entrar en modo demo": muestra el incidente de duplicacion
reconstruido (mismo dataset que tests/fixtures/dupe_incident.json en
services/engine).

## Build

    npm run build

Salida en dist/ (estatico, apto para CDN).
