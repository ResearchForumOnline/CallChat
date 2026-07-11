# ZMath media E2EE profile

CallChat's hosted web client can require the shared ZMath passphrase and exact
pattern image for voice calls, video calls, and screen sharing. This is an
additional factor layered into the existing MatrixRTC and LiveKit frame E2EE
path, not a replacement for it.

## Protection model

The browser prepares a room-scoped media factor from the shared passphrase and
exact pattern. The embedded call engine combines that factor with the rotating
MatrixRTC media-key path before LiveKit frame encryption is applied to audio,
video, and screen sharing.

Both the ZMath factor and the normal MatrixRTC media context are required. This
keeps the additional factor layered on top of the established call stack
without publishing private ZMath policy or deployment material.

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
