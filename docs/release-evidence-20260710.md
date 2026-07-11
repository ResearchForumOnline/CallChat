# CallChat Security Release Evidence - 2026-07-10

> Historical record: the simulator receipt described here was later superseded
> by the optional operational QPU-factor profile. See
> [Operational QPU Factor Release Evidence](release-evidence-20260711-qpu-factor.md).

This note records the public, reproducible evidence for the July 2026 security baseline. It intentionally contains no credentials, server addresses, room identifiers, access tokens, signing keys, or private deployment paths.

## Shipped Baseline

- All rooms existing at deployment time had `m.room.encryption` configured with `m.megolm.v1.aes-sha2`.
- The hosted Zero Bot moved to `matrix-nio[e2e]`, persists its crypto store with owner-only permissions, refuses unencrypted rooms, and requires an explicit allowlist.
- The hosted Element profile prefers owner-controlled MatrixRTC authorization and SFU infrastructure for calls.
- The ZShield browser workspace protects messages, files, and vault notes locally as authenticated ZME1 containers.
- Public account creation can use Synapse's server-backed reCAPTCHA UI-authentication stage plus registration rate limits.
- An optional server-side IonQ v0.4 simulator hook can issue assurance receipts; it remains outside encryption key material and receives no plaintext.
- Public AI security and call answers read state-backed status rather than repeating generic product copy.

Room encryption is not retroactive. Messages sent before encryption was enabled keep their original historical protection state.

## ZME1 Test Evidence

Run from the repository root:

```bash
node web/public/shield/app/zshield-core.test.mjs
```

The suite covers:

- encrypt/decrypt round trip;
- wrong passphrase rejection;
- authenticated-header tamper rejection;
- required pattern-factor rejection;
- excessive PBKDF2 work-factor rejection;
- malformed IV rejection;
- truncated ciphertext rejection;
- known-answer vector interoperability.
- chat-message envelope round trip and `ZSHIELD1:` decoding;
- authenticated ZMath policy and Matrix transport context;
- malformed or altered message-envelope rejection;
- bounded envelope size and fingerprint generation.

The profile is defined in [zme1-public-profile-v1.md](zme1-public-profile-v1.md). It uses AES-256-GCM, PBKDF2-HMAC-SHA-256 at 600,000 iterations, a random 128-bit salt, a random 96-bit IV, a 128-bit tag, and the canonical header as additional authenticated data.

## Honest Limits

- ZME1 is not an independent cryptographic certification.
- It does not protect a compromised endpoint, hide metadata, provide revocation, or recover forgotten secrets.
- Matrix E2EE, ZShield files, and WebRTC call media are separate layers with separate threat models.
- Stock Element does not automatically apply ZShield. A sender protects a message in the ZShield workspace and pastes the resulting envelope into an encrypted Matrix room; the recipient opens it in the workspace.
- IonQ receipts are optional research evidence. They do not add entropy to or derive ZShield keys, and IonQ is not in the required encryption path.
- The PQC roadmap proposes future hybrid ML-KEM work after review; it is not represented as deployed call-media encryption.
- Premium policy, managed recovery, entitlement services, production secrets, and private ZMath research are not in this repository.
