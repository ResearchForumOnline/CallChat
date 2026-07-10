# Matrix CAPTCHA Registration

CallChat uses Synapse's user-interactive authentication flow instead of a
client-side puzzle. The browser first posts the requested username and
password with `inhibit_login: true`. Synapse returns a session and an
`m.login.recaptcha` stage. The browser renders the public reCAPTCHA site key,
then submits the token against that same UIA session.

Security properties:

- the reCAPTCHA private key remains only in the Synapse configuration;
- the public page never stores a Matrix access token;
- `inhibit_login: true` sends the new user to the normal Element login flow;
- Synapse rate limits registration independently of the browser UI;
- production deployments should add moderation, abuse reporting, and optional
  email verification according to their threat model.

The sanitized Synapse template includes placeholder keys and conservative
registration limits. Never commit a real reCAPTCHA secret.
