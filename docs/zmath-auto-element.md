# ZMath Auto for Element

CallChat's hosted Element client includes an optional, browser-side ZMath Auto
layer for text and file payloads. It does not call an AI API and plaintext is not
sent to a ZMath server.

## What it does

After a local unlock, the controller intercepts Element's message composer and
attachment picker. Text becomes a `ZSHIELD1:` envelope and files become `.zme1`
containers before Element sends them. Matching incoming envelopes and files can
be opened locally while the same factors are unlocked.

The current public profile is `ZMATH-PBKDF2-HKDF-AESGCM-2`:

- PBKDF2-SHA-256 derives a password factor using 600,000 iterations.
- SHA-256 binds the exact pattern-image bytes as a second factor.
- HKDF-SHA-256 mixes independent factors with a per-container salt.
- AES-256-GCM encrypts and authenticates the payload and header context.
- The legacy `ZSHIELD-PBKDF2-AESGCM-1` profile remains readable.

The pattern image can be remembered only as an AES-GCM-encrypted local browser
record. The passphrase remains in memory for the unlocked session and is not
stored. Recipients need the same passphrase and exact image to open the extra
application layer.

## Honest security boundary

This is an application-layer control above Matrix. Matrix room encryption and
device verification remain important. Calls use MatrixRTC/WebRTC with their
standard transport protections; this repository does not claim that live audio
or video is quantum encrypted. IonQ experiments are optional research receipts,
not encryption keys and not a replacement for reviewed cryptography.

The integration source is in [`element/zmath-auto`](../element/zmath-auto/).
Run its contract test and the cryptographic tests with:

```bash
node element/zmath-auto/zmath-auto.test.mjs
node web/public/shield/app/zshield-core.test.mjs
```
