# CallChat One-Reply and Automatic Protection Release Evidence

Date: 2026-07-11

Release: `callchat-2026.07.11.8`

Client module revision: `2026.07.11-auto8`

## Shipped capability

- Zero Bot atomically claims each Matrix event before generating a reply.
- Matrix sends use a deterministic transaction ID derived from the originating
  event, so a retry resolves to the original send instead of creating another.
- Immediate duplicate client sends from the same room member are coalesced by a
  short prompt window.
- Edited messages and notice events do not trigger new bot answers.
- Bot answers are related to the originating event for a clear one-input,
  one-reply timeline.
- Multiline messages containing an explicit `!zero` command route only that
  command; ambient handling cannot produce a second path for the same event.
- Security, privacy, billing, Q-Call, and service-status answers use a
  professional product voice without inherited joke or gimmick copy.
- ZMath presents one primary automatic-protection action by default.
- The trusted-device profile is encrypted with a non-exportable AES-GCM browser
  key and restored automatically on later visits from the same browser profile.
- Shared-profile import, session-only use, Matrix-only sending, reset, and the
  authenticated encryption self-test are grouped under Advanced options.
- Both maintained Element paths use the same controller and cache version.

## Privacy and security boundary

The bot ledger stores only SHA-256 digests, state, and timestamps in its
owner-only crypto directory. It does not persist room plaintext, raw Matrix
event IDs, room IDs, or user IDs.

Trusted-device auto-unlock follows the security boundary of the signed-in
browser profile. Recovery factors remain necessary for another browser or
device, and approved participants need the same passphrase and exact pattern to
open the additional ZMath layer. Matrix E2EE and device verification remain the
transport foundation.

No production credential, server address, Matrix token, API key, recovery
factor, private ZMath source, or backup is included in this evidence record.

## Reproducible validation

| Suite | Result |
| --- | --- |
| Event replay, prompt coalescing, release, retention, and transaction tests | 6 passed |
| Command precedence and intentional health-check tests | 4 passed |
| Encrypted transport contract tests | 4 passed |
| Runtime replay test through the live transport module | 2 passed |
| ZMath Element interception contract | passed |
| ZMath authenticated 1 KB browser round trip | passed |
| One-click setup, reload auto-restore, and device reset browser flow | passed |
| JavaScript and Python syntax checks | passed |

The runtime replay test delivered the same event twice and a second event with
the same command to the encrypted transport. Exactly one Matrix send was
produced. A different command produced one additional send, and an edit
produced none.

## Public reference files

- [`ai/callchat-zero-bot/event_guard.py`](../ai/callchat-zero-bot/event_guard.py)
- [`ai/callchat-zero-bot/test_event_guard.py`](../ai/callchat-zero-bot/test_event_guard.py)
- [`ai/callchat-zero-bot/zero_matrix_bot.py`](../ai/callchat-zero-bot/zero_matrix_bot.py)
- [`ai/callchat-zero-bot/zero_matrix_bot_e2ee.py`](../ai/callchat-zero-bot/zero_matrix_bot_e2ee.py)
- [`element/zmath-auto/zmath-auto.js`](../element/zmath-auto/zmath-auto.js)
- [ZMath Auto for Element](zmath-auto-element.md)
