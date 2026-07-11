# Owner-Managed AI and Quantum Assurance

CallChat can route approved site-agent and assurance work through a local
OpenZero service, OpenAI, or Groq. The server owner also chooses whether IonQ
assurance receipts are disabled, submitted to the simulator, or submitted to
an explicitly approved QPU backend.

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
| IonQ | Quantum job receipt for a non-secret assurance commitment | Backend and paid-QPU approval |

`ai/provider_control.py` provides the reference implementation. Provider URLs
are fixed in code, model IDs and backend IDs are validated, and API keys are
kept server-side. Public status responses contain only configured and enabled
state, never the key value or a derivative of it.

## AI + IonQ Assurance Flow

1. CallChat builds a non-secret manifest describing the enabled protection
   layers and provider-isolation controls.
2. The selected AI route reviews only that manifest and returns a concise
   operator check.
3. CallChat serializes the manifest and review and creates a SHA-256
   commitment.
4. IonQ receives the commitment as job metadata with a small QIS circuit.
5. CallChat records the IonQ job ID, backend, status, and commitment as the
   assurance receipt.

Encryption does not wait for or depend on the provider result. The receipt is
an auditable assurance record around the security controls; client-side ZShield
and Matrix encryption continue independently.

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
- Require a separate owner confirmation before enabling a paid IonQ QPU.
- Do not log provider keys, visitor prompts, passphrases, patterns, Matrix keys,
  ZME1 content, or protected payloads.
- Rotate a provider key immediately if it appears in a room, screenshot, log,
  issue, commit, or support message.

The example environment file is
[`ai/zero-agent-bridge.example.env`](../ai/zero-agent-bridge.example.env).
