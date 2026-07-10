# CallChat Zero Bot Bridge

This folder contains the runnable Matrix bot bridge for `@zero:callchat.org`.

The production transport uses `matrix-nio` with a persistent Olm/Megolm store.
It refuses unencrypted rooms and refuses an allow-all room policy. Matrix room
encryption remains the base security layer; ZShield `.zme1` containers add a
separate local protection path for selected files and vault notes.

The bot is designed to run as a normal Matrix account, answer only in approved rooms, use OpenZero as the preferred local AI brain, and use Voicebox as an optional local speech backend.

## What It Does

- Joins CallChat rooms as `@zero:callchat.org`.
- Responds to `!zero` commands and direct mentions.
- Uses local OpenZero first through an OpenAI-compatible endpoint.
- Can ask Voicebox to generate speech when a user runs `!zero voice ...`.
- Keeps room memory in RAM only by default.
- Avoids reading private encrypted rooms unless a room deliberately invites and configures the bot.
- Does not include Matrix tokens, passwords, API keys, or ZMath private implementation details.

## Guardrail Shape

Zero Bot can be sharp, funny, sarcastic, and rebellious against boring defaults. It must not become an uncontrolled public nuisance.

The public default is:

- no spam;
- no harassment, threats, hate, doxxing, or sexual content with minors;
- no help stealing accounts, breaking into systems, or exposing secrets;
- no raw Shield secrets, pattern material, recovery phrases, database credentials, signing keys, or API keys in prompts;
- no hidden training on rooms;
- no long-term room memory unless a future admin feature explicitly enables it.

## Install Sketch

On the server, place the runnable folder somewhere private, for example:

```bash
sudo mkdir -p /opt/callchat-zero-bot
sudo cp zero_matrix_bot_e2ee.py requirements.txt callchat_knowledge.json /opt/callchat-zero-bot/
sudo python3 -m venv /opt/callchat-zero-bot/.venv
sudo /opt/callchat-zero-bot/.venv/bin/pip install -r /opt/callchat-zero-bot/requirements.txt
sudo chown -R root:root /opt/callchat-zero-bot/.venv
sudo chmod -R a+rX /opt/callchat-zero-bot/.venv
```

Put secrets outside the repo:

```bash
sudo useradd --system --home-dir /nonexistent --shell /usr/sbin/nologin callchat-bot
sudo install -d -o root -g callchat-bot -m 750 /etc/callchat-zero-bot
sudo install -o root -g callchat-bot -m 640 .env.example /etc/callchat-zero-bot/bot.env
sudo install -d -o callchat-bot -g callchat-bot -m 700 /opt/callchat-zero-bot/store
```

Edit `/etc/callchat-zero-bot/bot.env` and set:

- `MATRIX_USERNAME`
- `MATRIX_PASSWORD` or `MATRIX_ACCESS_TOKEN`
- `CALLCHAT_BOT_ALLOWED_ROOMS`
- `OPENZERO_LLM_URL`
- `OPENZERO_MODEL`
- `OPENZERO_API_KEY` when OpenZero requires one
- `VOICEBOX_URL` when voice output is installed

Then install the systemd template from `systemd/callchat-zero-bot.service`.

## Rate Limits

Default live behavior gives each user five quick replies per room, then a short cooldown. This keeps the vibe visible without letting one person turn the room into bot spam.

Environment knobs:

```text
CALLCHAT_BOT_USER_RATE_BURST=5
CALLCHAT_BOT_USER_RATE_WINDOW_SECONDS=60
CALLCHAT_BOT_ROOM_RATE_BURST=40
CALLCHAT_BOT_ROOM_RATE_WINDOW_SECONDS=60
CALLCHAT_BOT_RATE_NOTICE_SECONDS=60
CALLCHAT_BOT_RATE_EXEMPT_USERS=
```

Use `CALLCHAT_BOT_RATE_EXEMPT_USERS` only for trusted Matrix IDs. The default should stay non-empty enough for demos and strict enough for public rooms.

## Recommended First Room

Start with one intentionally approved encrypted bot room. The E2EE bot refuses rooms without `m.room.encryption` and refuses an allow-all room policy.

```text
#zero-bot-lab:callchat.org
```

Invite `@zero:callchat.org` and test:

```text
!zero help
!zero about
!zero status
!zero openzero
!zero voice
!zero voice Say CallChat ZERO is online.
```

## OpenZero Defaults

The bot expects OpenZero at:

```text
http://127.0.0.1:1024/v1/chat/completions
```

Choose a CPU-first model that fits the server's measured memory and latency budget, for example:

```text
qwen3:4b
```

If the owner's current Fable model performs better on the live machine, set `OPENZERO_MODEL` to that model name instead. Keep models within the server's memory budget and avoid oversized models for public chat.

## Voicebox Defaults

The bot expects Voicebox at:

```text
http://127.0.0.1:17493/generate
```

Voice is command-based by default. This prevents the bot from creating audio for every message in a public room.

## Useful Commands

```text
!zero callchat
!zero openzero
!zero frontdesk
!zero voice
!zero rules
!zero status
!zero explain-shield
```

`!zero status` uses a fast endpoint reachability check so it stays responsive even before OpenZero or Voicebox are installed.

## Changed Files / Logs

Do not log room plaintext, bot tokens, API keys, passwords, recovery phrases, Shield secrets, or private source paths.
