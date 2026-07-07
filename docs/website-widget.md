# Website Widget

The CallChat Zero Agent widget lets an existing website show a compact support/AI assistant.

## Use Cases

- Explain how to connect with Element.
- Explain server setup.
- Route users to docs.
- Answer product questions through an approved OpenZero bridge.
- Show that the deployment has a live AI path without exposing admin tools.

## Install

```bash
bash scripts/callchatctl.sh install-widget /var/www/example.com/public
```

The command:

- backs up the webroot;
- copies CSS/JS assets;
- injects a marked snippet into `index.html` when safe.

## Backend

The widget expects a JSON endpoint:

```http
POST /api/zero-agent
Content-Type: application/json

{"message":"How do I connect Element?","source":"example.com"}
```

Expected response:

```json
{"reply":"Install Element, choose custom homeserver, and enter example.com."}
```

Keep the backend rate limited and locked to approved sites.
