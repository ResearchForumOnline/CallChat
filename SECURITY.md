# Security Policy

## Reporting

Report security issues privately through the contact route on https://callchat.org/.

Do not post passwords, Matrix access tokens, recovery phrases, private keys, signing keys, database details, or exploit-ready details in public issues or pull requests.

## Supported Scope

This repository is a public self-host kit. It contains templates and documentation. It does not contain production secrets or private Shield implementation code.

Security reports are useful for:

- Unsafe public templates.
- Missing hardening guidance.
- Insecure default examples.
- Leaky documentation.
- Broken access-control assumptions.
- Cross-site scripting or injection issues in the public website templates.

## Never Commit

- `.env` files with real values.
- Matrix signing keys.
- Synapse shared registration secrets.
- PostgreSQL passwords.
- Matrix account credentials.
- API keys or SSH keys.
- Access tokens.
- Production backups.
- Private Shield/ZMath source.
- Premium entitlement internals.

## Baseline Hardening

- Keep registration closed or token/invite controlled.
- Keep PostgreSQL private to Docker/internal networks.
- Put Synapse behind HTTPS.
- Back up before upgrades.
- Test restore before depending on backups.
- Restrict admin endpoints and admin users.
- Use TURN for calls, but keep TURN credentials and shared secrets private.
- Pin versions, then update promptly for security fixes.

## Shield Boundary

Public materials describe Shield behaviour, user flows, and licensing boundaries only. Real security must rely on strong cryptographic design and key handling, not on hiding source code alone.

If private Shield/ZMath implementation, production configuration, or recovery material appears in this repository, report it privately and do not quote, mirror, fork, or attach the material to a public issue.
