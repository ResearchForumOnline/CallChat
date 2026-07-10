# IonQ Research Receipts

CallChat's optional IonQ integration submits a small QIS circuit to the IonQ
v0.4 `simulator` backend. The browser creates a random local nonce, sends only
its SHA-256 commitment to the server, and receives an IonQ job receipt. ZShield
can authenticate that receipt inside the envelope context.

This path is deliberately outside the encryption key schedule:

- no plaintext, passphrase, pattern file, AES key, salt, or IV is sent to IonQ;
- a failed or unavailable IonQ service does not weaken normal ZShield encryption;
- the receipt is research/attestation metadata, not quantum encryption;
- simulator use is the default; QPU submission is not exposed to public clients;
- the API key remains in a protected server-side environment file.

The public bridge accepts `POST /v1/quantum/ionq/receipt` with:

```json
{"commitment":"64-lowercase-hex-characters"}
```

Deployments should add strict per-IP and global rate limits at the reverse
proxy, keep the endpoint same-origin, and monitor IonQ quota. The hosted UI
also labels the option as research evidence rather than key material.

IonQ's current API contract is documented at:
<https://docs.ionq.com/api-reference/v0.4/jobs/create-job>.
