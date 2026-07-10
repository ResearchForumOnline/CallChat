# ZShield Threat Model v1

## Protected Assets

- File or vault-note plaintext.
- Passphrase and optional pattern bytes.
- Derived AES key.
- Integrity of authenticated payload and metadata.

## Adversaries Considered

- A Matrix server, storage provider, proxy, or backup operator that obtains the
  ZME1 attachment but not the local secrets.
- A network attacker that obtains the container through transport compromise.
- A recipient or storage system that accidentally modifies the container.
- A public-site visitor attempting to make the AI agent overstate security.

## Guarantees

- Plaintext is encrypted before the container is downloaded or attached.
- AES-GCM detects modification to ciphertext or authenticated header fields.
- Every production container receives a random salt and IV.
- The hosted app does not submit passphrases, pattern bytes, or plaintext.
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
- Publish reproducible test vectors without production keys or server details.

## Residual Risks

PBKDF2 is intentionally expensive but remains vulnerable to offline guessing
when users choose weak passphrases. Browser memory may retain plaintext until
garbage collection. ZME1 v1 is a working profile, not an independently audited
cryptographic product certification.
