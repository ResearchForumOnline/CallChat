# ZMath Auto for Element

CallChat's hosted Element client includes an optional, browser-side ZMath Auto
layer for text and file payloads. It does not call an AI API and plaintext is not
sent to a ZMath server.

## What it does

After a local unlock, the controller intercepts Element's message composer while
the maintained CallChat client routes every room upload through the ZMath bridge.
That native upload point covers the file picker, drag and drop, paste, and
composer file insertion. Text becomes a `ZSHIELD1:` envelope and files become
`.zme1` containers before Element sends them. Matching incoming envelopes and
files can be opened locally while the same factors are unlocked.

The hosted build marks ZMath as required before Element starts. In Shield mode,
a missing or locked bridge blocks the upload instead of silently sending the
original file. Plain Matrix uploads remain available only through the explicit
Matrix-only switch.

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

`Create secure setup automatically` generates a random grouped passphrase and a
unique PNG pattern locally, downloads the pattern, remembers only its encrypted
device record, and unlocks the current session. The passphrase is shown once and
must be stored separately. `Run encryption self-test` performs an authenticated
random-payload round trip with the current factors without uploading plaintext.

## How to verify an uploaded file

After Matrix decrypts an event, a ZMath-protected attachment should have:

- `body` ending in `.zme1`;
- `info.mimetype` equal to `application/json`;
- a downloaded JSON container whose header profile is
  `ZMATH-PBKDF2-HKDF-AESGCM-2` and payload kind is `matrix-attachment`.

Matrix may then encrypt that `.zme1` file again for transport, so its event can
still contain Matrix's `A256CTR` encrypted-file structure and the original event
can still be a Megolm `m.room.encrypted` event. The distinguishing evidence is
that the inner attachment is a ZME1 container. An event whose decrypted body is
still the original `.docx`, image, or other filename used Matrix protection only.

## Honest security boundary

This is an application-layer control above Matrix. Matrix room encryption and
device verification remain important. Calls use MatrixRTC/WebRTC with their
standard transport protections; this repository does not claim that live audio
or video is quantum encrypted. IonQ experiments are optional research receipts,
not encryption keys and not a replacement for reviewed cryptography.

The integration source is in [`element/zmath-auto`](../element/zmath-auto/).
The native upload choke point is published in CallChat Community commit
[`303b65b`](https://github.com/ResearchForumOnline/CallChat-Community/commit/303b65b4e5fedb38c252767555b2e699b7c6180b).
Run its contract test and the cryptographic tests with:

```bash
node element/zmath-auto/zmath-auto.test.mjs
node web/public/shield/app/zshield-core.test.mjs
```
