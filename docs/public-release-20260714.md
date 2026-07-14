# Protected Rooms, Call Audio, and Signup Release

Date: 14 July 2026

This hosted release improves protected-room onboarding, remote call-audio
recovery, account creation, and narrow-screen usability. It publishes verified
behaviour and limitations, not licensed Shield/ZMath source, production
configuration, or private research.

## Protected-room experience

- Replaces independent per-browser protection profiles with an explicit,
  room-scoped setup and approval flow carried inside the Matrix encrypted room.
- Shows separate status for the Matrix room, Matrix identity, local recovery
  vault, and optional ZMath room key so users can see which layer needs action.
- Gives a new browser a clear **Request protected access** action and gives an
  existing key holder an explicit approval step.
- Keeps protected transport envelopes out of the normal timeline, including
  replies and recycled timeline items, and shows a recovery action when the
  room key is unavailable.
- Binds additional protection to the room profile. A profile from another room
  or an independently generated legacy profile cannot silently open it.

Existing protected messages still require the profile that created them. This
release does not weaken or bypass that rule when an older profile is missing.

## Calls

- Detects when a browser has accepted remote media but blocked audible playback.
- Presents a responsive **Enable sound** control that resumes audio from the
  user gesture required by Safari and other autoplay-restricted browsers.
- Keeps the existing MatrixRTC/LiveKit encoded-frame encryption path intact.
- When the optional protected-room layer is active, call media keys remain
  bound to that room profile without sending the profile secret to the media
  service.

CallChat does not describe this WebRTC media path as quantum encryption. The
live security claim is the deployed, testable encrypted-media path stated
above.

## Signup and mobile usability

- Normalizes Matrix usernames to lowercase while typing and disables mobile
  keyboard autocapitalization for the field.
- States the 12-to-128-character password requirement beside the fields.
- Shows both password fields while typing by default, with a visible control to
  hide them again.
- Retains the same-origin local arithmetic CAPTCHA and rotates cached signup
  assets so browsers receive the current validation behaviour.
- Keeps the signup form and active chat panel usable without horizontal
  overflow on narrow mobile screens.

## Validation

- Passed the focused call-audio component suite (17 tests), type checking,
  linting, formatting, and a production call build.
- Passed signup UI and backend boundary tests, including 11, 12, 128, and 129
  character password cases.
- Passed protected-message, room-approval, file-container, and media-key
  contract checks against both local and hosted assets.
- Verified the hosted release manifest, security headers, service health,
  source-map exclusion, bot-room replies, mobile layout, and the two-copy
  recovery policy.

An audible two-person call remains the final device-level confirmation because
speaker routing and browser permissions belong to each participant's device.

## Public boundary

The community repository includes capability descriptions, deployment
guidance, and open-source client modifications required by their licences. It
does not include hosted credentials, server addresses, account data, production
backups, private key derivation, licensed Shield/ZMath implementation modules,
or proprietary recovery logic.
