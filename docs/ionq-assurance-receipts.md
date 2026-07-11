# Operational IonQ QPU Factor

CallChat can create an optional hardware-linked factor for ZShield and ZMath.
This replaces the earlier receipt-only design: when a hardware `.zqf` file is
loaded, its 256-bit factor is an actual required input to message, file, and
call-root key derivation. A missing or incorrect factor fails closed.

## Protocol

1. The browser creates a 256-bit random nonce with `crypto.getRandomValues`.
2. Only the nonce's SHA-256 commitment is sent to the CallChat owner service.
3. The service submits an eight-qubit Hadamard circuit with 512 shots to an
   owner-approved IonQ hardware backend through API v0.4.
4. After completion, the service validates the probability result and returns
   a domain-separated SHA-512 measurement digest plus bounded job evidence. It
   also verifies that IonQ's stored job metadata contains the same browser
   commitment and protocol-purpose markers before accepting the result.
5. The browser verifies its nonce commitment and applies HKDF-SHA-512 to the
   local nonce using the measurement digest as salt and the backend, job ID,
   and commitment as context.
6. The resulting 256-bit factor is saved locally as a `.zqf` file. The final
   factor is never sent to IonQ or the CallChat service.
7. ZShield includes the factor digest and job-evidence digest in authenticated
   container metadata and mixes the factor digest into its KDF. ZMath Auto also
   mixes the factor into its room media root before per-room call keys are
   derived.

The simulator follows the same API contract for testing, but produces a
`.zqf-test` file that the production hardware profile rejects.

## Security meaning

This is a **QPU-linked independent encryption factor**, not quantum key
distribution and not a claim that IonQ performs encryption. The local nonce is
the factor's secret input. The hardware result changes the derived factor and
provides auditable provider evidence, but it must not be represented as
certified quantum randomness or as a replacement for standardized
post-quantum key establishment.

The factor file is a recovery secret. Share it separately from ciphertext and
protect it like a key. Anyone who has the `.zqf`, passphrase, and exact pattern
can open matching content.

## Provider boundary

- IonQ receives no plaintext, passphrase, pattern, Matrix key, media key,
  encryption key, local nonce, or final factor.
- The IonQ API key remains in a mode-`0600` server-side provider store.
- Hardware jobs require both an owner-level paid-QPU permission and a separate
  confirmation for each submission.
- The browser control route is owner-authenticated, same-origin, rate-limited,
  POST-only, and non-cacheable.
- Closing the owner tab before a job completes discards its pending local nonce;
  that job then cannot produce a factor and must not be reused.

IonQ API references:

- <https://docs.ionq.com/api-reference/v0.4/jobs/create-job>
- <https://docs.ionq.com/api-reference/v0.4/jobs/get-job>
- <https://docs.ionq.com/api-reference/v0.4/results/get-results-by-job-id>

The standardized post-quantum upgrade track is documented in
[ZShield PQC Roadmap](zshield-pqc-roadmap.md).
