# Deployment Notes

This guide contains public deployment information only. Never paste real secrets into GitHub.

## Website

Deploy `web/public` to the document root for your public domain.

Before deploying:

- Back up the current webroot.
- Back up reverse proxy config.
- Confirm rollback path.
- Confirm `.well-known` JSON.
- Confirm HTTPS certificates.

## Synapse

Use PostgreSQL for production.

Keep:

- registration closed or invite/token controlled
- database port private
- Synapse admin endpoints restricted
- backups encrypted/private
- `server_name` unchanged after launch

## Reverse Proxy

Use either:

- `infra/synapse/reverse-proxy-apache-example.conf`
- `infra/synapse/reverse-proxy-nginx-example.conf`

Adapt domains and certificate paths before use.

## Healthcheck

Run:

```bash
bash scripts/healthcheck.sh https://example.com https://matrix.example.com
```

Expected checks:

- `https://example.com/.well-known/matrix/client`
- `https://example.com/.well-known/matrix/server`
- `https://matrix.example.com/_matrix/client/versions`

## Calls

Configure TURN/coturn before promising reliable voice/video. Test across mobile data, home Wi-Fi, and at least one stricter network.
