# ZMath Automatic Protection Release - 2026-07-11

TalkToAI ZMath now supports a one-click local setup and automatic file workflow at
`https://talktoai.org/zmath/portable/` and `https://talktoai.org/zmath/exclusive/`.

## Live capabilities

- Generates a 39-character passphrase and unique 512-pixel pattern image locally.
- Downloads a recovery kit containing both factors for offline storage.
- Remembers factors in an AES-GCM-encrypted, device-bound browser vault.
- Automatically encrypts a selected source file and decrypts a selected matching container.
- Restores another device by importing the recovery kit.
- Uses no AI API for generation, encryption, decryption, or local recovery.
- Raises the default work factor for new containers to 600,000 PBKDF2-SHA-256 iterations.
- Retains compatibility with older containers whose recorded work factor is within safety limits.
- Adds file, container, version, mode, metadata, and KDF resource bounds before expensive work.

The recovery kit is intentionally sensitive: anyone holding it can recreate both
factors. It should be stored offline and separately from encrypted containers.

## Customer-funded IonQ receipts

`https://talktoai.org/zmath/quantum/` provides a deployment-ready evidence lane.
A customer server can hash a ZME1 container locally and submit only its SHA-256
commitment in metadata attached to an IonQ v0.4 job. The resulting job ID, status,
backend, commitment, and submission time form an external provenance receipt.

The endpoint requires a server-side customer IonQ key and a separate deployment
access token. It includes same-origin enforcement, an explicit QPU enable switch,
a serialized daily job limit, backend allowlisting, and request-size limits. No
IonQ credential is placed in public JavaScript.

TalkToAI itself does not currently have this paid lane configured. Its endpoint
reports that state and fails closed. A quantum-cloud receipt is not an encryption
key, not quantum key distribution, and not evidence that live calls are quantum
encrypted. ZME1 confidentiality continues to come from local authenticated
cryptography; IonQ provides optional customer-funded provenance evidence.

## Validation

- JavaScript syntax and automatic-workflow contract tests passed locally and during deployment.
- The IonQ authorization, cost-control, and public-secret boundary test passed.
- PHP syntax checks ran on the production server before installation.
- Live Portable, Exclusive, policy, quantum-status, cache, desktop, and mobile checks passed.
- Deployment uses file-level rollback and retains only the two newest snapshots.
