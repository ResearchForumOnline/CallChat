# Admin Guide

## Launch Defaults

- Keep public registration closed.
- Create users manually or through controlled invite/token flows.
- Create a small admin room for notices and support.
- Enable media size limits that match your disk budget.
- Keep logs useful but avoid logging secrets.

## User Creation

From the Synapse container:

```bash
docker compose exec synapse register_new_matrix_user -c /data/homeserver.yaml http://localhost:8008
```

Create only the accounts you need. Store admin credentials in a password manager.

## Moderation

Prepare:

- Abuse report route.
- Room admin rules.
- Spam response plan.
- Account suspension process.
- Backup and restore process.

## Backups

Back up:

- PostgreSQL.
- Synapse config.
- Signing keys.
- Media store.
- Reverse proxy configs.
- Web discovery files.

Never publish backups in GitHub.
