# Local CAPTCHA Registration

This service provides a same-origin account-creation boundary for deployments
that do not want a third-party CAPTCHA dependency. It issues short arithmetic
questions, keeps each answer only in server memory, binds the challenge to the
client IP, expires it after five minutes, and consumes it after one attempt.

Successful checks create a non-admin Matrix account through Synapse's local
shared-secret registration endpoint. The browser receives only the Matrix user
ID; no access token or registration secret is returned.

Production controls include:

- exact same-origin enforcement through an Nginx-set internal header;
- Nginx request limits plus service-side hourly attempt limits;
- strict username and password bounds;
- a 4 KiB request-body limit;
- a dedicated unprivileged systemd user and read-only filesystem policy;
- no external CAPTCHA API, cookies, analytics, or browser storage.

Store the Synapse registration secret outside the web root at
`/etc/callchat-register/registration-secret`, readable only by the service
account. Keep native public Synapse registration disabled so the protected
service is the only public account-creation path.

Run the unit tests with:

```bash
python3 -m unittest discover -s registration/local-captcha -p 'test_*.py' -v
```

The arithmetic question is intentionally a low-friction human check. Rate
limits and moderation remain necessary because no simple challenge alone can
stop determined automated abuse.
