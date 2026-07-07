# CallChat Community

Self-hosted Matrix chat with a CallChat front door, a branded Element Web profile, Synapse/PostgreSQL templates, voice/video notes, and a clean public boundary for optional premium Shield features.

![CallChat preview](https://callchat.org/assets/images/callchat-og-20260707.webp)

## What This Repo Gives You

- A cloneable starter kit for a CallChat-style homeserver.
- Synapse + PostgreSQL Docker templates.
- Apache and Nginx reverse proxy examples.
- Matrix `.well-known` discovery examples.
- Element Web configuration and CallChat theme hooks.
- A PHP/HTML/CSS/JS landing page that works on Apache/CWP style hosting.
- Scripts for health checks, backups, and release packaging.
- Docs for DNS, installation, admin tasks, Element setup, TURN calls, updates, and public safety boundaries.
- Optional AI bot integration notes for OpenZero-style local agents.

## What This Repo Does Not Include

This public repository does not include private deployment material:

- ZMath / CallChat Shield implementation source.
- Matrix signing keys.
- Database passwords.
- Synapse shared registration secrets.
- Matrix access tokens.
- SSH keys, API keys, or server credentials.
- Production backups.
- Private entitlement or licensing code.

Standard Matrix chat can be self-hosted from this repo. Premium Shield behaviour is documented only at a safe product level.

## Architecture

CallChat Community keeps the proven Matrix stack and wraps it in a CallChat deployment layer:

- `callchat.org` style public domain: website, docs, downloads, `.well-known`, and optional hosted web client.
- `matrix.example.com` style API domain: Synapse client/server API behind HTTPS.
- Synapse: Matrix homeserver.
- PostgreSQL: production database.
- Element Web: Matrix-compatible web client, configured and themed for the deployment.
- TURN/coturn: voice/video relay for real-world networks.
- Optional Zero Bot: a consent-based Matrix bot that can connect to OpenZero or another local LLM bridge.

## Quick Start

1. Copy `.env.example`:

   ```bash
   cp infra/synapse/.env.example infra/synapse/.env
   ```

2. Edit the values for your domain. Do not reuse the example passwords.

3. Generate a Synapse config for your final server name:

   ```bash
   cd infra/synapse
   docker compose run --rm synapse generate
   ```

4. Start the stack:

   ```bash
   docker compose up -d
   ```

5. Put the web files under your public web root and expose the Matrix reverse proxy.

6. Run the health check:

   ```bash
   bash scripts/healthcheck.sh https://example.com https://matrix.example.com
   ```

Read [docs/install.md](docs/install.md) before production use.

## Element Compatibility

CallChat does not replace the Matrix protocol. It gives a CallChat-branded route into it.

Users can connect with:

- Hosted Element Web.
- Official Element Android/iOS/desktop clients.
- Other compatible Matrix clients.
- Future CallChat-native clients.

For security and licensing hygiene, this repo configures and themes upstream Element Web instead of hiding upstream code inside CallChat.

## Update Policy

You can pin versions for stability, but do not freeze security-critical software forever. Synapse, Element Web, Docker images, and OS packages receive security updates. The recommended model is:

- Pin exact versions in production.
- Test updates in staging.
- Back up before upgrades.
- Roll forward promptly for security fixes.
- Keep CallChat branding/config separate from upstream code.

See [docs/update-policy.md](docs/update-policy.md).

## Shield Boundary

CallChat Shield / ZMath is an optional premium vault layer for protected files and advanced workflows. This public repo describes:

- User-facing behaviour.
- Safe integration boundaries.
- Licensing model.
- What clients should show when a Shield file is present.

It does not publish the proprietary implementation. See [docs/zmath-boundary.md](docs/zmath-boundary.md).

## License

CallChat Community files in this repository are released under the MIT License unless a file states otherwise.

Third-party projects such as Synapse, Element Web, Matrix SDKs, Docker images, and operating system packages keep their own licenses. Check [NOTICE.md](NOTICE.md) before redistributing combined builds.
