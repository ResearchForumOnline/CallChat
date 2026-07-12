# ZShield Threat Model v1

## Protected Assets

- File or vault-note plaintext.
- User recovery material.
- Derived content keys.
- Integrity of authenticated payload and metadata.

## Adversaries Considered

- A Matrix server, storage provider, proxy, or backup operator that obtains the
  ZME1 attachment but not the local secrets.
- A network attacker that obtains the container through transport compromise.
- A recipient or storage system that accidentally modifies the container.
- A public-site visitor attempting to make the AI agent overstate security.

## Guarantees

- Plaintext is encrypted before the container is downloaded or attached.
- Authenticated encryption detects modification before content is opened.
- Production containers use fresh per-item randomness.
- The hosted app does not submit recovery material or plaintext to AI providers.
- Current CallChat rooms use Matrix E2EE independently of ZShield.

## Non-Goals

- Protection after an endpoint is compromised or unlocked.
- Protection from malicious browser extensions, keyloggers, or screen capture.
- Concealing filename, size, type, timestamp, or attachment presence.
- Recovering data after all secrets are lost.
- Revoking a portable file already received by another party.
- Claiming live audio is quantum encrypted.

## Operational Controls

- Serve the app over HTTPS with restrictive security headers.
- Keep Matrix device verification enabled.
- Refuse unencrypted rooms in Zero Bot.
- Keep MatrixRTC, TURN, Synapse, and the ZShield app independently testable.
- Keep premium test vectors, derivation details, and implementation source out of public distributions.

## Residual Risks

Weak user secrets remain vulnerable to guessing. Browser memory may retain
plaintext until garbage collection. Shield is not represented as independently
certified cryptographic hardware or as a substitute for external review.
