# Hellshade-bot
[![Docker](https://github.com/Natsku123/Hellshade-bot/actions/workflows/docker-publish.yml/badge.svg?branch=main)](https://github.com/Natsku123/Hellshade-bot/actions/workflows/docker-publish.yml)

Discord bot with some Dota 2 related features and Discord activity experience.

## Features

Most significant features of Hellshade-bot.

### Discord activity levels

Every Guild Member collects experience based on their activity in the guild.
Experience is collected by reacting, sending messages and participating in 
voice chats. Voice chat activity grants double experience on weekends (Friday 
17:00 - Sunday 23:59 UTC) to help people unable to participate on work days.

#### Voice chat experience formula

`ceil(M * (N / 4 * 5))` where `M` is the multiplier (1 on workdays and 2 on 
weekends) and `N` is the number of users on the voice channel. Voice chat 
experience is calculated every `60s`.

#### Level generation formula

##### Level 1
First level is always `1000` experience.

##### Level 2-90
`ceil(1000 + 1.2 * (value - 1) ** 2)`

##### Level >90
`ceil(1000 + 1024 * (value - 1) ** 0.5)`

### Games

Gaming / Game specific features

#### Dota 2

##### Random hero

By using `!dota_random` one can get a 'truly random' hero in response, if 
the in-game random button is not enough random for you. The heroes and 
their info are updated daily.

##### Patch note fetching - EXPERIMENTAL
Currently, the bot SOMETIMES succeeds fetching patch notes for Dota 2 and 
is able to post them on a hardcoded channel.

#### Steam news

Steam news subscriptions by Steam AppId are supported.

More info: `!help steam news`

### Roles

Role assignment system with reactions and a generated message that will be 
updated if necessary.

More info: `!help role`

#### Subcommands

##### Add

Add author to specified role by role name.

Usage:
`!role add <role name>`

##### Remove

Remove author from specified role by role name.

Usage:
`!role remove <role name>`

##### Create - Admin only

Add a new role to be assignable on the server. Emoji can be added, so 
reactions are enabled.

Usage:
`!role create <role id> <description> [emoji]`

##### Delete - Admin only

Delete a role from assignable roles.

Usage:
`!role delete <role id>`

##### Update - Admin only

Update role description.

Usage:
`!role update <role id> <description>`

##### Init - Admin only

Initialize role reaction message on current channel. Role reaction message 
can be overridden by running the command again.

Usage:
`!role init`

## Migration from `origin/main`

This branch replaces the legacy Vue dashboard and FastAPI/GraphQL backend with
the Next.js dashboard in `webui/`. It also moves the bot runtime from the
requirements-based workflow to Python 3.13 and `uv`.

### Before deploying

1. Install Docker Compose and, for local development, Python 3.13 with `uv`
	and Yarn.
2. Remove any deployment references to the deleted `frontend/` and `backend/`
	applications. The replacement dashboard is the `webui` service and source
	directory.
3. Replace GraphQL reads used by the old dashboard with these HTTP endpoints:
	`GET /api/health`, `GET /api/servers`, `GET /api/servers/:id`, and
	`GET /api/levels`.
4. Set the environment values used by Compose: `TOKEN`, `OWNER`, `ADMINS`,
	`DB_NAME`, `DB_USER`, and `DB_PASS`. The Web UI receives its database
	connection through the `DB_*` values. When running it outside Compose, use
	either `DATABASE_URL` or `DB_HOST`, `DB_USER`, `DB_PASS`, and `DB_NAME` in
	`webui/.env.local`.

### Database migration

The bot container runs `uv run alembic upgrade head` on startup, so existing
Alembic revisions apply automatically. This branch also adds the
`gw2_tp_orders` model, but does not include its Alembic revision. Create and
review that revision before deploying the model to a database:

```bash
docker compose run --rm bot uv run alembic revision --autogenerate -m "add gw2 tp orders"
docker compose run --rm bot uv run alembic upgrade head
```

Commit the generated revision with the deployment change. Do not rely on
autogeneration against a production database without reviewing the SQL.

### Start and verify

Build and start the replacement stack from the repository root:

```bash
docker compose up --build -d
```

The Web UI is available directly on `http://localhost:3000`; the stack also
includes Traefik for HTTP routing. For local Web UI development, run:

```bash
yarn --cwd webui install --ignore-engines
yarn --cwd webui dev
```

Validate the migration with:

```bash
docker compose ps
curl --fail http://localhost:3000/api/health
uv run pytest
yarn --cwd webui lint
yarn --cwd webui test
```