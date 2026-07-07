# Synapse Deployment Template

This folder contains production-shaped templates for a Matrix homeserver.

## Server Name Warning

Choose `SERVER_NAME` before launch and do not change it later. Matrix user IDs, room IDs, federation identity, and client discovery all depend on it.

Recommended pattern:

- Public identity: `example.com`
- Matrix API host: `matrix.example.com`
- `.well-known` on `https://example.com`

## First-Time Setup

1. Copy the environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env`.

3. Generate Synapse config:

   ```bash
   docker compose run --rm synapse generate
   ```

4. Merge safe values from `homeserver.yaml.template` into the generated `/data/homeserver.yaml`.

5. Start services:

   ```bash
   docker compose up -d
   ```

6. Watch logs:

   ```bash
   docker compose logs -f synapse
   ```

## Create First Admin User

After Synapse is running:

```bash
docker compose exec synapse register_new_matrix_user -c /data/homeserver.yaml http://localhost:8008
```

Use a strong password and store it safely.

## Registration Policy

Keep public registration disabled unless you have spam controls and moderation ready.

Suggested launch options:

- Admin-created accounts.
- Token/invite registration.
- Manual account review.

## Backups

Back up before any update:

- PostgreSQL dump.
- Synapse data volume.
- Media store.
- Reverse proxy config.
- `.well-known` files.

Test restore on a separate machine before relying on the backup.
