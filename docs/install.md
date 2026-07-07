# Install Guide

This guide describes a public CallChat Community deployment. Replace `example.com` with your real domain.

## Requirements

- Linux server.
- DNS control for your domain.
- Docker and Docker Compose.
- Apache or Nginx reverse proxy.
- HTTPS certificates.
- SMTP provider if you enable email flows.
- TURN/coturn server for reliable voice/video calls.

## Domain Model

Recommended:

- `example.com`: public website, Matrix discovery, optional hosted Element Web.
- `matrix.example.com`: Synapse Matrix API.

For a very small deployment, you can reverse proxy Matrix under the public domain too. A separate Matrix API host is cleaner long term.

## Steps

1. Point DNS records.
2. Deploy `web/public` to the public web root.
3. Replace `.well-known/matrix/client` and `.well-known/matrix/server` with your real Matrix API host.
4. Copy `infra/synapse/.env.example` to `.env`.
5. Set a final `SERVER_NAME`.
6. Generate Synapse config.
7. Configure PostgreSQL.
8. Put Synapse behind Apache or Nginx.
9. Create the first admin account.
10. Keep registration closed until moderation and anti-abuse are ready.
11. Configure TURN/coturn for calls.
12. Test Element login from mobile and desktop.

## Critical Warning

Do not change Synapse `server_name` after launch. It becomes part of Matrix user IDs and federation identity.
