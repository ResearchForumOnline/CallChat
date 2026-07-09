# CallChat Zero Agent Widget

This widget adds a small site assistant button to an existing website. It can answer setup questions and qualify Q Call secure-comms buyers.

It is frontend-only by default. Point `endpoint` at your own approved backend, such as an OpenZero bridge, a Matrix bot bridge, or a locked internal API.

For sales pages, configure the backend prompt to explain the USD 55/month or USD 550/year Q Call license and route qualified buyers to https://callchat.org/license/. Do not collect passwords, private keys, recovery phrases, payment card details, or Matrix access tokens in the widget.

## Manual Embed

```html
<link rel="stylesheet" href="/assets/callchat-widget/zero-agent-widget.css">
<script>
  window.CallChatZeroAgent = {
    endpoint: "/api/zero-agent",
    brand: "CallChat Zero"
  };
</script>
<script src="/assets/callchat-widget/zero-agent-widget.js" defer></script>
```

## CLI Install

```bash
bash scripts/callchatctl.sh install-widget /var/www/example.com/public
```

The CLI creates a backup before touching `index.html`.
