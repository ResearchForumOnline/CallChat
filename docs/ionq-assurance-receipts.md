# IonQ Assurance Receipts

CallChat's IonQ integration submits a small QIS circuit through the IonQ v0.4
API. The default backend is the simulator; a server owner can explicitly allow
a supported QPU. IonQ receives a SHA-256 commitment and returns a traceable job
receipt that CallChat can bind to a ZShield assurance record.

The provider boundary is strict:

- no plaintext, passphrase, pattern file, AES key, salt, or IV is sent to IonQ;
- a failed or unavailable IonQ service does not weaken normal ZShield encryption;
- the receipt records the quantum assurance job while encryption remains client-side;
- simulator use is the default and a paid QPU requires explicit owner approval;
- the API key remains in a protected server-side environment file.

The public bridge accepts `POST /v1/quantum/ionq/receipt` with:

```json
{"commitment":"64-lowercase-hex-characters"}
```

Deployments should add strict per-IP and global rate limits at the reverse
proxy, keep the endpoint same-origin, monitor IonQ quota, and never expose QPU
selection on a public unauthenticated route.

The owner control-plane design and AI review sequence are documented in
[Owner-Managed AI and Quantum Assurance](owner-provider-control.md).

IonQ's current API contract is documented at:
<https://docs.ionq.com/api-reference/v0.4/jobs/create-job>.
