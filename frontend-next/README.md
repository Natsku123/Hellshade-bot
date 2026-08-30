# Hellshade Next

Next.js + TypeScript replacement for the legacy Vue frontend and FastAPI GraphQL backend.

## Stack

- Next.js App Router
- TypeScript
- Yarn
- PostgreSQL via `pg`

## Environment

Copy `.env.local.example` to `.env.local` and set either:

1. `DATABASE_URL`
2. `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME`

## Local development

```bash
yarn install --ignore-engines
yarn dev
```

Open `http://localhost:3000`.

## API routes

- `GET /api/health`
- `GET /api/servers`
- `GET /api/servers/:id`
- `GET /api/levels`

These routes replace the previous GraphQL reads used by the old dashboard views.

## Build

```bash
yarn lint
yarn build
```

## Docker

Use the root-level `docker-compose-next.yml` to run bot + db + traefik + this Next app.
