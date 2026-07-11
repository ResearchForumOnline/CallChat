# Matrix Local CAPTCHA Registration

CallChat's local registration boundary avoids third-party CAPTCHA scripts and
verification APIs. The browser requests a same-origin arithmetic challenge,
then submits the username, password, challenge ID, and answer to the local
service over HTTPS.

The answer is never encoded into the public challenge. It remains in service
memory, is bound to the client IP, expires after five minutes, and is consumed
on the first registration attempt. The service validates input and creates a
non-admin user through Synapse's loopback-only shared-secret endpoint.

The public response contains only the new Matrix user ID. It does not expose a
Matrix access token, Synapse registration secret, password, challenge answer,
or administrative capability.

Deployment requirements:

- keep native public Synapse registration disabled;
- store the registration secret outside the web root with service-only read
  permission;
- expose only the two exact Nginx locations in the provided example;
- overwrite the internal same-origin header at the reverse proxy;
- retain both Nginx and application rate limits;
- monitor registrations and keep an abuse-response process.

The included unit tests cover one-time use, expiry, client binding, incorrect
answers, account validation, and the Synapse registration MAC protocol.
