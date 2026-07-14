# Automatic Protected Rooms, Calls, Signup, and Help Release

Date: 14 July 2026

This hosted release improves protected-room onboarding, remote call-audio
recovery, account creation, task-based help, and narrow-screen usability. It
publishes verified behaviour and limitations, not licensed Shield/ZMath
source, production configuration, or private research.

## Protected-room experience

- Replaces independent per-browser protection profiles with room-scoped
  profiles coordinated inside the Matrix-encrypted conversation.
- Makes protected-chat setup and matching-profile synchronization automatic
  for ordinary use. Layer status, diagnostics, and manual recovery remain
  available under Advanced options.
- Recovers automatically from short sign-in or room-navigation timing gaps.
  When an older profile is no longer available from any active room device,
  CallChat can establish fresh protection for new traffic without discarding
  the draft or repeatedly asking the sender to retry.
- Keeps the authenticated profiles a trusted device has learned for a room,
  allowing newly established traffic and later-recovered history to coexist
  instead of repeatedly replacing one another.
- Preserves an in-progress device access request across a normal page reload
  where the browser supports protected local storage, and serializes the
  short synchronization operations so they cannot overwrite a user's draft.
- Confirms the visible signed-in conversation before every protected send and
  repairs stale room navigation when the active room can be identified safely.
- Verifies each protected message with a local encrypt-and-open round trip
  before the client allows it to leave the composer.
- Keeps protected transport and synchronization envelopes out of the normal
  timeline, including replies and recycled timeline items.
- Keeps one visible plaintext result for each successfully opened event, even
  when the timeline presents the same event through nested display layers.
  Hidden transport content remains hidden after a full reload.
- Selects the current message in a reply instead of accidentally rendering a
  quoted older envelope.
- Collapses repeated notices for unavailable legacy history into one clear
  summary while new matching messages continue to open normally.
- Binds additional protection to the room profile. A profile from another room
  or an independently generated legacy profile cannot silently open it.

Existing protected messages still require the profile that created them. This
release does not weaken or bypass that rule when an older profile is missing.
Starting fresh protection affects new traffic only and does not rewrite or
claim to recover historical ciphertext.

## Calls

- Detects when a browser has accepted remote media but blocked audible playback.
- Presents a responsive **Enable sound** control that resumes audio from the
  user gesture required by Safari and other autoplay-restricted browsers.
- Keeps the existing MatrixRTC/LiveKit encoded-frame encryption path intact.
- When the optional protected-room layer is active, call media keys remain
  bound to that room profile without sending the profile secret to the media
  service.
- Holds a protected call at the readiness step when the browser knows it does
  not yet have the room's current authenticated profile, preventing a call
  from starting with a mismatched additional factor.

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

## Help and Shield interface

- Rebuilds the Help center around real tasks: the first three minutes, Shield
  status, a new phone or browser, common faults, calls, and account recovery.
- Adds searchable questions and topic filters so users can search for the
  words they see on screen instead of learning internal terminology first.
- Explains the Matrix room, Matrix identity, local vault, and protected-chat
  states in plain language, with a clear everyday path that requires no manual
  Shield key steps.
- Keeps the normal Shield panel focused on current status and direct help.
  Legacy recovery, optional factors, reset controls, diagnostics, and technical
  references remain grouped under progressively disclosed Advanced options.
- Restores the branded hosted-app entrypoint and verifies that its referenced
  compiled assets exist before release. The same gate follows the active entry
  bundle when checking the protected call bridge, preventing a stale or missing
  bundle reference from producing an empty client.
- Keeps the compatibility client available while directing the primary hosted
  experience to the branded CallChat Shield application.

## Validation

- Passed the focused call-audio component suite (17 tests), type checking,
  linting, formatting, and a production call build.
- Passed signup UI and backend boundary tests, including 11, 12, 128, and 129
  character password cases.
- Passed protected-message, room-approval, file-container, and media-key
  contract checks against both local and hosted assets.
- Passed an isolated two-browser synchronization check covering automatic
  request, encrypted approval, profile installation, reply handling, draft
  preservation, reload persistence, and plaintext rendering.
- Passed an unavailable-profile recovery check covering delayed account
  readiness, one synchronization request, one protected send, local opening,
  and an immediate follow-up without another request.
- Verified the hosted release manifest, security headers, service health,
  source-map exclusion, bot-room replies, mobile layout, and the two-copy
  recovery policy.
- Verified a newly protected production message appeared once as plaintext,
  remained readable after a full page reload, and left no pending protection
  state or visible transport envelope.
- Verified Help search and filters and checked Help, manuals, guide, hosted app,
  and Shield layouts at 360, 390, 768, and 1440 pixel widths without page
  overflow or off-screen controls.
- Verified the pinned `2026.07.14.15` hosted client, its release-integrity lock,
  and the synchronized `/app/` and `/element/` protection assets.

An audible two-person call remains the final device-level confirmation because
speaker routing and browser permissions belong to each participant's device.

## Public boundary

The community repository includes capability descriptions, deployment
guidance, and open-source client modifications required by their licences. It
does not include hosted credentials, server addresses, account data, production
backups, private key derivation, licensed Shield/ZMath implementation modules,
or proprietary recovery logic.
