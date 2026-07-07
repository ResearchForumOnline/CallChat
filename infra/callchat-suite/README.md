# CallChat Suite Compose

This compose file groups the public services most self-hosters expect:

- PostgreSQL.
- Synapse.
- Optional local Element Web static server.

OpenZero is installed through the OpenZero project installer rather than vendored here. That keeps the AI node update path clear and avoids copying a second project into this repo.

## Typical Flow

```bash
bash scripts/callchatctl.sh wizard
bash scripts/callchatctl.sh install-element
docker compose -f infra/callchat-suite/docker-compose.yml --profile element up -d
```

Then reverse proxy:

- Matrix API to Synapse on `127.0.0.1:8008`.
- Element Web to `127.0.0.1:8088`.
- Public website from `web/public`.

Keep the real `.env`, generated Synapse config, signing keys, and backups out of GitHub.
