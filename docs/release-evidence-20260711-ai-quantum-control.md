# CallChat AI + Quantum Control Release Evidence

> Historical record: the receipt-only IonQ design in this release was
> superseded on 2026-07-11 by the operational QPU-factor profile documented in
> [Operational QPU Factor Release Evidence](release-evidence-20260711-qpu-factor.md).

Date: 2026-07-11

Release: `callchat-2026.07.11.7`

## Shipped Capability

- Owner-selectable AI routing across local OpenZero, OpenAI, and Groq.
- Server-side API key storage with `0700` directory and `0600` file policy.
- Redacted provider status that returns configured and enabled state, never the
  key value or a derivative of it.
- Fixed provider endpoints, bounded model identifiers, bounded request bodies,
  and cloud fallback to the owner-controlled local route.
- Secret-pattern detection that keeps likely passwords, API keys, Matrix
  tokens, private keys, and recovery phrases on the local OpenZero route.
- IonQ v0.4 assurance jobs with simulator default and explicit paid-QPU owner
  approval.
- AI + IonQ assurance sequence: non-secret manifest, AI review, SHA-256
  commitment, IonQ job receipt.
- Matrix registration enabled in the maintained CallChat client profile.
- Complete Synapse UI-auth registration sequence for deployments that require
  `m.login.recaptcha` followed by `m.login.dummy`.

## Provider Isolation

The provider lane receives none of the following:

- ZMath passphrases;
- exact pattern images or pattern bytes;
- Matrix Olm/Megolm keys;
- ZMath room media factors;
- protected-message or file plaintext;
- ZME1 payloads;
- provider keys belonging to another provider.

ZShield and Matrix encryption remain client-side and independent of provider
availability. IonQ receives the assurance commitment, not encryption key
material.

## Reproducible Tests

The release passed:

| Suite | Result |
| --- | --- |
| Provider control and key-store tests | 7 passed |
| Public bridge, origin, secret-routing, and IonQ tests | 15 passed |
| ZShield message/file round trip, tamper, factor, and resource bounds | passed |
| ZMath Auto Element interception contract | passed |
| CallChat Community distribution contract | passed |
| CallChat Shield showcase assembly contract | passed |
| JavaScript syntax checks | passed |
| JSON validation | passed |
| Server-side PHP lint and render gate | passed |

The provider tests include negative cases for an unconfigured route, a disabled
active route, unapproved paid-QPU selection, invalid commitments, cross-origin
requests, key redaction, and provider-key exclusion from request bodies.

## Public Reference Files

- [`ai/provider_control.py`](../ai/provider_control.py)
- [`ai/zero_agent_bridge.py`](../ai/zero_agent_bridge.py)
- [`ai/test_provider_control.py`](../ai/test_provider_control.py)
- [`ai/test_zero_agent_bridge.py`](../ai/test_zero_agent_bridge.py)
- [Owner-Managed AI and Quantum Assurance](owner-provider-control.md)
- [IonQ Assurance Receipts](ionq-assurance-receipts.md)

No API key, server credential, Matrix token, signing key, private ZMath source,
production backup, or private deployment configuration is included in this
evidence record.
