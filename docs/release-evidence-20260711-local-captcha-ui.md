# Local CAPTCHA and Welcome UI Release Evidence - 2026-07-11

## Registration boundary

The hosted account centre uses the public `CALLCHAT-LOCAL-CAPTCHA-1`
implementation. It loads no third-party CAPTCHA script or verification API.
Challenges are one-time, held in service memory, bound to the client address,
expire after five minutes, and are protected by reverse-proxy and service-side
rate limits.

Native public Synapse registration is disabled. After a successful challenge,
the loopback service delegates the protocol operation to Synapse's installed
registration helper and requests a non-admin account. Browser responses contain
the Matrix user ID and do not contain a Matrix access token or registration
secret.

## Client UI

The fixed client command bar and Element auth viewport now share one height
contract, keeping the welcome footer inside the viewport. The Create account
action and direct registration route both lead to the protected account centre.
The signup card remains page-scrollable when its fields exceed the viewport.

## Verification

- Eight local registration state and HTTP-boundary tests passed.
- Cross-site challenge requests and native Matrix registration returned 403.
- A solved challenge reached Synapse and an existing-user check returned the
  expected conflict without creating a test account.
- The registration listener was verified on loopback only.
- The protected secret file was verified as service-group-readable, not public.
- No current registration, Synapse, or version-lock error entries remained.
- Version-lock verification passed across 15 application and registration files.
- ZMath Auto, ZShield, QPU-factor, and community-client contracts passed.
