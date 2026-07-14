# ZShield Post-Quantum Roadmap

The production claim today is deliberately narrow: Shield uses established
classical authenticated encryption. It is not labelled post-quantum public-key
cryptography.

## Research direction

- Evaluate standardized NIST post-quantum key establishment and signatures.
- Preserve cryptographic agility, explicit versioning, and downgrade resistance.
- Keep identity, key lifecycle, backup, recovery, and revocation inside the
  review scope rather than treating an algorithm swap as a complete product.
- Keep experimental profiles, private test vectors, and implementation details
  outside the public community repository.

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
