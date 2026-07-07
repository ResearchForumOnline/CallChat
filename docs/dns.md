# DNS and Discovery

## Public Website

Create an `A` or `AAAA` record:

```text
example.com -> your server IP
```

## Matrix API Host

Create:

```text
matrix.example.com -> your server IP
```

## Client Discovery

Serve this from:

```text
https://example.com/.well-known/matrix/client
```

```json
{
  "m.homeserver": {
    "base_url": "https://matrix.example.com"
  }
}
```

## Server Delegation

Serve this from:

```text
https://example.com/.well-known/matrix/server
```

```json
{
  "m.server": "matrix.example.com:443"
}
```

## HTTPS

Use HTTPS for both the public website and Matrix API host. Matrix clients expect reliable TLS.
