# Operational QPU Factor Release Evidence - 2026-07-11

## Delivered behavior

- Owner-authenticated IonQ v0.4 submit and status lifecycle.
- Eight-qubit Hadamard circuit, 512 requested shots, strict result validation,
  and domain-separated result hashing.
- Browser-local 256-bit nonce; only its SHA-256 commitment leaves the browser.
- Local HKDF-SHA-512 derivation of a 256-bit `.zqf` factor.
- QPU-factor ZShield messages and files fail closed without the matching factor.
- ZMath Auto mixes the factor into its call media root before deriving
  room-scoped MatrixRTC/LiveKit frame-encryption material.
- Simulator output is marked test-only and rejected by the hardware profile.
- Paid hardware execution requires owner permission plus per-job confirmation.
- Polling rejects a job whose IonQ-stored client commitment or protocol-purpose
  metadata does not match the browser request.

## Verified tests

| Suite | Result |
| --- | --- |
| Provider control and bridge | 18 passed |
| ZShield round-trip, tamper, missing/wrong factor | Passed |
| QPU factor derivation, evidence tamper, simulator boundary | Passed |
| ZMath Auto integration contract | Passed |

The IonQ simulator was used to validate the external API contract. No paid
hardware job is represented by this test record.

## Claim boundary

This release makes IonQ output an operational input to the optional factor
profile rather than a decorative receipt. It does not implement quantum key
distribution, certify the cloud result as private quantum entropy, or replace
NIST ML-KEM key establishment. The secret contribution is the browser-local
nonce; IonQ and the CallChat server do not receive the final factor.

See [Operational IonQ QPU Factor](ionq-assurance-receipts.md) for the protocol
and [ZShield PQC Roadmap](zshield-pqc-roadmap.md) for the ML-KEM release gates.
