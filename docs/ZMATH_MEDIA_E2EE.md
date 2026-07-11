# ZMath media E2EE profile

CallChat's hosted web client can require the shared ZMath passphrase and exact
pattern image for voice calls, video calls, and screen sharing. This is an
additional factor layered into the existing MatrixRTC and LiveKit frame E2EE
path, not a replacement for it.

## Key hierarchy

1. The browser hashes the exact pattern image with SHA-256.
2. It combines that hash with the passphrase using PBKDF2-SHA-256 at 600,000
   iterations and HKDF-SHA-256 to create a session media root.
3. HKDF-SHA-256 derives a distinct 256-bit factor for each Matrix room.
4. The embedded call engine HKDF-mixes that factor with every rotating
   MatrixRTC sender key, participant identity, and key index.
5. LiveKit's frame E2EE worker uses the resulting key material for audio,
   video, and screen-sharing frames.

Both the ZMath room factor and the normal rotating MatrixRTC key are required.
A different passphrase, pattern, room, participant, sender key, or key index
produces different media key material.

## Secret handling

The room factor stays in browser memory. It is not put in an iframe URL,
Matrix event, widget data, local storage, server request, or telemetry payload.
The embedded call reads it directly from its same-origin parent. Byte arrays
are zeroed when ZMath is locked, Matrix-only mode is selected, or a new session
is unlocked. Hosted calls fail closed if the required bridge is missing or
locked.

The hosted distribution enables Matrix group calls and sets Element Call to
exclusive mode, including for two-person rooms. This prevents a fallback to
the legacy one-to-one WebRTC call path, which does not implement this custom
profile.

## Compatibility and limits

This profile currently works only between matching CallChat web clients.
Unmodified Element and Matrix clients cannot decrypt a ZMath-protected
CallChat call.

This is classical authenticated media encryption built with Web Crypto,
MatrixRTC, and LiveKit frame E2EE. It is not a post-quantum key exchange and it
does not claim quantum security. Independent cryptographic review is required
before high-assurance use.

The matching media-engine source is published in the
[`ResearchForumOnline/element-call`](https://github.com/ResearchForumOnline/element-call)
fork, and the parent call gate is in
[`ResearchForumOnline/CallChat-Community`](https://github.com/ResearchForumOnline/CallChat-Community).
