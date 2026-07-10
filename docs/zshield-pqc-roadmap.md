# ZShield Post-Quantum Roadmap

The production claim today is deliberately narrow: ZME1 v1 uses AES-256-GCM
for local authenticated payload encryption. It is not labelled post-quantum
public-key cryptography.

## Proposed v2 Research Profile

1. Generate a random 256-bit content-encryption key per payload.
2. Keep AES-256-GCM for the payload.
3. Wrap the content key with a hybrid classical plus NIST ML-KEM mechanism.
4. Bind recipient identifiers, algorithms, encapsulations, and key identifiers
   into authenticated metadata.
5. Optionally sign evidence manifests with ML-DSA or SLH-DSA after a separate
   identity and key-lifecycle review.
6. Preserve explicit algorithm identifiers and fail closed without downgrade.

## Release Gates

- Standards-conformant library with active maintenance.
- Known-answer and negative vectors on browser, Android, iOS, Linux, macOS, and
  Windows implementations.
- Independent cryptographic design review.
- Documented key rotation, backup, recovery, revocation, and migration.
- Performance and maximum-payload measurements on target devices.
- Public limitations that distinguish research from deployed guarantees.

No website or agent may call ZShield post-quantum encrypted until these gates
are met for a deployed profile.
