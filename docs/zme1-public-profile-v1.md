# ZME1 Public Profile v1

Status: working interoperability profile for the CallChat ZShield hosted MVP.

## Scope

ZME1 is an authenticated container for a file or UTF-8 vault note. The hosted
workspace creates and opens the container in the browser. Plaintext,
passphrases, and optional pattern bytes are not sent to CallChat by the
workspace.

ZME1 is additive to Matrix E2EE. It does not replace Matrix room encryption,
device verification, or DTLS-SRTP for calls.

## Profile Identifier

`ZSHIELD-PBKDF2-AESGCM-1`

## Container Shape

The UTF-8 JSON object contains:

- `header`: authenticated metadata and algorithm parameters.
- `ciphertext`: standard Base64 of AES-GCM ciphertext with the 128-bit tag
  appended by Web Crypto.

The header contains `format`, `version`, `profile`, `payload`, `createdAt`,
`kdf`, and `cipher`. Implementations must reject unknown format, version,
profile, KDF, cipher, or tag-length values.

Filename, media type, size, payload kind, creation time, algorithms, salt, IV,
and pattern-required flag are visible metadata. They are authenticated but not
encrypted.

## Canonical Header

Authenticated additional data is the UTF-8 encoding of the header serialized
as JSON with object keys sorted lexicographically at every depth, no added
whitespace, and normal JSON array order.

## Key Derivation

1. Require a passphrase of at least 14 Unicode code units in the v1 UI.
2. Compute `pattern_digest = SHA-256(pattern_bytes)` when a pattern is used.
3. Otherwise use 32 zero bytes as `pattern_digest`.
4. Build `material = UTF8(passphrase) || 0x00 || pattern_digest`.
5. Apply PBKDF2-HMAC-SHA-256 with a random 128-bit salt and 600,000 iterations. Importers reject values above 1,200,000 to prevent attacker-controlled resource exhaustion.
6. Derive a 256-bit AES key.

The pattern file is a second secret factor, not a password-strength substitute.

## Encryption

- Algorithm: AES-256-GCM.
- IV: 96 random bits for every container.
- Authentication tag: 128 bits.
- Additional authenticated data: canonical header bytes.
- Randomness source: operating-system-backed Web Crypto `getRandomValues`.

Implementations must never reuse an IV with the same key and must release no
plaintext when GCM authentication fails.

The hosted profile accepts payloads up to 50 MiB and requires decoded ciphertext to equal the authenticated payload size plus the 16-byte GCM tag. Salt and IV fields must decode to exactly 16 and 12 bytes respectively.

## Interoperability

The public known-answer fixture is
`shield/app/test-vectors/zme1-v1.json`. It contains test-only credentials and
plaintext. Production code must never reuse its salt or IV.

## Security Boundary

ZME1 v1 does not provide account recovery, remote revocation, hidden metadata,
malware protection, endpoint protection, or post-quantum public-key exchange.
An attacker with a container can perform offline passphrase guesses. Use a
long, unique passphrase and an optional high-entropy pattern file.
