# Architecture

## Purpose

CallChat Community is a deployment layer around the Matrix ecosystem. It keeps the compatibility benefits of Synapse and Element while adding a CallChat public website, branded client configuration, operator docs, and optional private integrations.

## Domain Pattern

Recommended:

- `example.com`: public landing page, docs, downloads, Matrix discovery, optional hosted Element Web.
- `matrix.example.com`: Matrix client/server API via Synapse.

Small deployments can proxy Matrix under the public domain, but a separate API host is easier to reason about.

## Runtime Layers

```text
Users
  |
  | Element / Matrix clients / hosted web
  v
Public HTTPS
  |-- example.com: website, downloads, .well-known
  |-- matrix.example.com: Synapse reverse proxy
       |
       | localhost/Docker network
       v
Synapse
  |
  | private Docker network
  v
PostgreSQL
```

## Matrix Layer

Synapse provides:

- Matrix identity and room state.
- Direct messages and group rooms.
- Media upload.
- Device verification.
- End-to-end encrypted room support through compatible clients.
- Admin/user management.
- Optional federation if enabled later.

PostgreSQL should be private. Do not expose the database port publicly.

## Client Layer

Element compatibility is intentional. Users should be able to connect using:

- Hosted Element Web.
- Element Android/iOS/desktop.
- Other Matrix-compatible clients.
- Future CallChat-native clients.

CallChat-specific UI should be added through configuration, themes, docs, and separate original client code. Avoid editing upstream client internals unless you are ready to track licensing and updates.

## Calls

Voice/video needs TURN/coturn for reliability. Without TURN, calls may work on some networks and fail on others.

## AI Layer

Optional Zero Bot style agents can join approved rooms and connect to a local OpenZero-compatible brain. The safe model is consent-based:

- Approved rooms only.
- Explicit opt-in.
- Clear bot identity.
- No secret logging.
- No private room scraping.
- Rate limits.
- Admin commands separated from user commands.

## Shield Boundary

CallChat Shield/ZMath is optional premium functionality above normal Matrix chat. The public repo can describe user-visible behaviour and safe integration points. It must not publish private source or entitlement internals.
