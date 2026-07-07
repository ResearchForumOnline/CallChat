# Element Setup

Users can connect with official Element clients while CallChat-native apps are developed.

## Mobile/Desktop

1. Install Element.
2. Choose a custom homeserver.
3. Enter your public domain, for example `example.com`.
4. If discovery is not ready, use `https://matrix.example.com`.
5. Sign in with the account created by your admin.

## Hosted Web Client

Deploy Element Web under a path such as:

```text
https://example.com/element/
```

Set `config.json` using `element/config.sample.json` as a starting point.

## Calls

Element calls need TURN relay for many real-world networks. Configure Synapse with TURN settings and test mobile-to-desktop, Wi-Fi-to-mobile, and restrictive-network scenarios.
