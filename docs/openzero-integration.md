# OpenZero Integration

CallChat can use OpenZero as the local AI brain for:

- a Matrix room bot;
- a public website assistant;
- voice replies when Voicebox or Piper is enabled;
- local OpenAI-compatible API calls;
- private operator workflows.

## Install OpenZero

From a CallChat checkout:

```bash
bash scripts/callchatctl.sh install-openzero
```

Or install from the OpenZero project directly:

```bash
curl -fsSL https://raw.githubusercontent.com/ResearchForumOnline/OpenZero/main/openzero/install.sh | bash
```

## Recommended Network Shape

- Keep the OpenZero Super Panel private.
- Expose only a narrow bridge endpoint for approved website/widget calls.
- Use local firewall rules, reverse proxy allowlists, or VPN/SSH tunnels for admin access.
- Use API keys where OpenZero requires them.
- Rate limit public widget traffic.

## Example Website Bridge

Copy the example env:

```bash
sudo mkdir -p /etc/callchat
sudo cp ai/zero-agent-bridge.example.env /etc/callchat/zero-agent.env
sudo editor /etc/callchat/zero-agent.env
```

Run directly for testing:

```bash
python3 ai/zero_agent_bridge.py
curl http://127.0.0.1:8787/health
```

For production, adapt:

```text
infra/systemd/callchat-zero-agent.service
```

Then reverse proxy only `/api/zero-agent` to `127.0.0.1:8787`.

## CallChat Zero Bot

The Matrix bot should run as a normal Matrix user, join approved rooms only, and call OpenZero through a private local endpoint.

Safe defaults:

- approved rooms only;
- visible bot identity;
- no secret logging;
- no hidden room training;
- rate limits;
- fallback answers when OpenZero is offline.

## Voice

OpenZero can route to Piper or Voicebox depending on what is installed. Public sites should mark generated speech clearly and rate-limit audio generation.
