# ZShield Policy Authorization Design

The hosted ZME1 v1 workspace has no server-side decryption factor. Future
Exclusive mode should add policy without sending plaintext or content keys to
the policy service.

## Proposed Flow

1. User authenticates with Matrix and requests a short-lived OpenID token.
2. Policy service validates the OpenID token against the declared homeserver.
3. Service checks license entitlement, deployment binding, expiry, and
   revocation.
4. Client sends a container identifier, algorithm profile, operation, and a
   fresh challenge. It does not send plaintext, passphrase, pattern bytes, or a
   derived content key.
5. Service returns a signed, short-lived policy assertion bound to the
   challenge, account, container, operation, and expiry.
6. Client verifies the assertion and combines policy with local key handling.

## Required Controls

- One-time challenges and short expiries.
- Signed assertions with versioned key identifiers.
- Rate limiting, replay detection, audit records, and revocation.
- No permissive Origin fallback and no bearer token in URLs.
- Separate production, test, and demo entitlement data.
- A documented offline and service-outage policy.

This design replaces the current experimental deterministic server-lock idea;
it must be implemented and reviewed before Exclusive mode is sold as active.
