# ZMath Auto for Element

CallChat's hosted Element client includes an optional, browser-side ZMath Auto
layer for text and file payloads. It does not call an AI API and plaintext is not
sent to a ZMath server.

## What it does

After automatic trusted-device restore or a shared-profile unlock, the controller intercepts Element's message composer while
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

For the default automatic mode, the browser generates a non-exportable AES-GCM
device key in IndexedDB and uses it to encrypt the local ZMath profile. The
encrypted profile record is stored in the same IndexedDB vault and automatically
restored on later visits from that trusted browser. Manual session-only import,
Matrix-only sending, reset, and the encryption diagnostic remain under
**Advanced options**. Legacy passphrase-encrypted pattern records remain
readable during manual recovery. Recipients
and approved devices still need the same passphrase and exact image to open the
extra application layer.

`Turn on automatic protection` generates a random grouped passphrase and a
unique PNG pattern locally, downloads the recovery pattern, encrypts the
trusted-device profile, and unlocks the session in one action. The passphrase
is shown once in the setup panel and must be stored separately from the pattern.
`Run encryption self-test` performs an authenticated random-payload round trip
with the current factors without uploading plaintext.

## Message rendering

Encrypted `ZSHIELD1` envelopes are hidden as soon as the client recognizes
them. The renderer creates one local display per Matrix event, marks an event
while decryption is in flight, opens newest messages first with bounded
concurrency, and replaces the placeholder in place. A mutation caused by the
local display cannot start a second decryption for the same event.

If the active profile does not match, the client shows one compact protected
message notice instead of exposing the full envelope. A profile-generation
counter prevents a decryption started under an old profile from appearing
after the user locks, resets, or changes profiles.

The one-time recovery code is removed from the DOM after it is copied, hidden
on request, and automatically cleared after 90 seconds.

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

## Security boundary

This is an application-layer control above Matrix. Matrix room encryption and
device verification remain important. The hosted protected-call profile uses a
required in-memory ZMath factor with rotating MatrixRTC media keys before
LiveKit frame encryption. An optional IonQ hardware-linked factor is mixed into
the ZMath media root before room keys are derived. The final factor remains
browser-local and must be distributed separately. This is not QKD. AI providers
remain separate from this operation and outside the encryption key path.

Trusted-device auto-unlock protects stored factors at rest but follows the
security boundary of the signed-in browser profile. Resetting site data removes
the automatic profile; recovery factors remain necessary for another browser
or device.

The integration source is in [`element/zmath-auto`](../element/zmath-auto/).
The native upload choke point is published in CallChat Community commit
[`303b65b`](https://github.com/ResearchForumOnline/CallChat-Community/commit/303b65b4e5fedb38c252767555b2e699b7c6180b).
Run its contract test and the cryptographic tests with:

```bash
node element/zmath-auto/zmath-auto.test.mjs
node web/public/shield/app/zshield-core.test.mjs
node web/public/shield/app/qpu-factor-core.test.mjs
```
