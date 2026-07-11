# Owner-Managed AI and QPU Factor Control

CallChat can route approved site-agent and assurance work through a local
OpenZero service, OpenAI, or Groq. Separately, the owner can use IonQ to create
a hardware-linked `.zqf` encryption factor or run the same contract against the
simulator without enabling the production hardware profile.

The provider lane is separate from the encryption lane. It does not receive
ZMath passphrases, exact pattern images, Matrix keys, call media factors,
protected-message or file plaintext, ZME1 payloads, or protected attachments.
Likely passwords, provider keys, Matrix tokens, private keys, and recovery
phrases are routed to local OpenZero instead of a cloud AI provider.

## Provider Routes

| Route | Purpose | Owner choice |
| --- | --- | --- |
| OpenZero | Local, owner-controlled AI and fallback replies | Default |
| OpenAI | Hosted model route for approved non-secret prompts | Model and enable state |
| Groq | Low-latency hosted model route for approved non-secret prompts | Model and enable state |
| IonQ | Hardware result contribution for a browser-derived `.zqf` factor | Backend, paid-QPU permission, and per-job approval |

`ai/provider_control.py` provides the reference implementation. Provider URLs
are fixed in code, model IDs and backend IDs are validated, and API keys are
kept server-side. Public status responses contain only configured and enabled
state, never the key value or a derivative of it.

## IonQ Factor Flow

1. The owner browser creates a 256-bit local nonce and submits only its SHA-256
   commitment.
2. The service submits a bounded QIS circuit to the configured IonQ backend.
3. On completion, the service validates the result and returns a
   domain-separated measurement digest and job evidence.
4. The browser verifies the commitment and derives the `.zqf` factor locally
   with HKDF-SHA-512.
5. ZShield and ZMath require that factor when a QPU-factor profile is selected.

The AI routes are not in this key path. The final factor, local nonce, content,
and ZMath recovery inputs are never sent to AI providers or IonQ.

## Environment Configuration

The public bridge supports environment configuration without credentials in
Git:

```dotenv
CALLCHAT_AI_PROVIDER=local
CALLCHAT_OPENAI_API_KEY=
CALLCHAT_OPENAI_MODEL=gpt-5.5
CALLCHAT_GROQ_API_KEY=
CALLCHAT_GROQ_MODEL=qwen/qwen3-32b
CALLCHAT_IONQ_API_KEY=
CALLCHAT_IONQ_BACKEND=simulator
CALLCHAT_IONQ_ALLOW_PAID_QPU=false
CALLCHAT_PROVIDER_STORE=/var/lib/callchat-openzero-bridge/provider-secrets.json
```

Use `gpt-5.6` only when the OpenAI project has access to that model. Use the
provider model-list test before activating a hosted route.

## Operator Requirements

- Run the bridge as a dedicated non-root service user.
- Keep the provider store directory mode `0700` and file mode `0600`.
- Put any browser control page behind strong authentication and same-origin
  write checks.
- Keep provider APIs on fixed allowlisted endpoints; do not accept arbitrary
  provider URLs from a browser form.
- Require saved owner permission and a separate confirmation for every paid
  IonQ QPU job.
- Do not log provider keys, visitor prompts, passphrases, patterns, Matrix keys,
  ZME1 content, or protected payloads.
- Rotate a provider key immediately if it appears in a room, screenshot, log,
  issue, commit, or support message.

The example environment file is
[`ai/zero-agent-bridge.example.env`](../ai/zero-agent-bridge.example.env).
