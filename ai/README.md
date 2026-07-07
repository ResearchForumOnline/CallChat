# AI Bot Integration

This folder describes optional AI agent integration. It does not include production tokens.

## Concept

A Matrix bot such as `@zero:example.com` can join approved rooms and answer support questions, summarize decisions, explain setup, and route users to docs.

## Safe Defaults

- Approved rooms only.
- Explicit opt-in.
- Clear bot identity.
- No hidden training on private rooms.
- No secret logging.
- Rate limits.
- Admin commands separated from normal user commands.

## OpenZero Bridge

Use a local OpenAI-compatible endpoint when available:

```text
POST http://127.0.0.1:11434/v1/chat/completions
```

Use your own endpoint and model. Keep API keys and bot tokens out of this repo.

## Website Agent Bridge

This repo includes a small dependency-free example:

- `ai/zero_agent_bridge.py`
- `ai/zero-agent-bridge.example.env`
- `infra/systemd/callchat-zero-agent.service`

It accepts widget messages, rate limits visitors, checks allowed origins, and forwards approved prompts to an OpenZero-compatible `/v1/chat/completions` endpoint when an API key is configured. Without an API key it returns safe product fallback answers.

Do not expose the OpenZero Super Panel publicly. Expose only this narrow bridge or a stronger production gateway.
