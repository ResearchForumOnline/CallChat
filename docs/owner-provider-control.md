# Owner-Managed Providers

CallChat Community can route approved, non-secret site-agent prompts through local OpenZero, OpenAI, or Groq. It can also submit separately bounded IonQ assurance jobs when an owner explicitly enables that provider.

## Public boundary

- Provider credentials stay in an owner-only server store or environment variable.
- Browser pages receive configured/enabled status, never credential values or derivatives.
- Matrix keys, recovery material, protected messages, protected files, and customer secrets are excluded from provider requests.
- Local OpenZero remains the fallback for prompts that resemble credentials or private material.
- Paid provider work requires an explicit owner setting; paid QPU work also requires per-job confirmation.
- The community bridge exposes assurance receipts only. Licensed Shield factor construction, derivation, recovery, and entitlement logic are not distributed here.

## Operator requirements

- Run the bridge as a dedicated non-root service user.
- Keep provider-store directories mode `0700` and files mode `0600`.
- Protect browser administration behind strong authentication and same-origin write checks.
- Use fixed provider endpoints rather than accepting arbitrary URLs.
- Do not log credentials, visitor prompts, recovery material, Matrix keys, or protected payloads.
- Rotate any credential that appears in a screenshot, issue, commit, room, or support message.

Configuration placeholders are documented in [`ai/zero-agent-bridge.example.env`](../ai/zero-agent-bridge.example.env). Real values must never be committed.
