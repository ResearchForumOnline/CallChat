# Message Renderer and Application Lock Evidence - 2026-07-11

## Renderer correction

The previous MutationObserver could schedule another room scan while a message
was still being decrypted. Because the rendered-display map was updated only
after the asynchronous KDF and decryption completed, several operations could
insert plaintext displays for one Matrix event.

The corrected renderer:

- marks each DOM body in a `WeakSet` before asynchronous work;
- selects one protected body per Matrix event tile, excluding nested wrappers;
- stages one placeholder and hides the envelope immediately;
- decrypts newest messages first, two at a time;
- updates the existing display instead of inserting another;
- collapses adjacent duplicate displays left by an interrupted render;
- rejects stale completions after a profile change or lock;
- replaces undecryptable envelopes with one compact protected-message notice.

A read-only production ledger check found one encrypted event at the timestamp
where the old browser displayed many copies, confirming that the duplication
was local rendering rather than repeated Matrix sends.

## Production application policy

The hosted deployment pins Synapse and Element application releases and does
not run automatic `pip`, Git, archive, container-tag, or APT upgrades for those
applications. A root-owned manifest records expected versions and hashes, with
a systemd path monitor and daily verification timer reporting drift.

OS and hosting-panel security updates remain enabled. Upstream application
security advisories must be reviewed and integrated through a tested release
bundle with backup and rollback rather than installed automatically.

## Verification

- ZMath Auto interception and renderer contract passed.
- ZShield and QPU-factor cryptographic tests passed.
- Live assets identify release `2026.07.11.10` and renderer `20260711-renderer2`.
- The version-lock check passed for Synapse `1.155.0`, Element Web `v1.12.23`,
  the CallChat release metadata, and eight pinned application files.
