# Public Publication Checklist

Use this checklist before publishing or updating the public CallChat repository.

## Must Stay Private

- Matrix signing keys, shared registration secrets, access tokens, and account credentials.
- Database credentials, database dumps, backups, logs, and server snapshots.
- Private Shield source, premium entitlement internals, and deployment-specific policy code.
- API keys, SSH keys, payment secrets, webhook secrets, or cloud credentials.
- Customer data, room exports, transcripts, media stores, or support records.
- Local build outputs, unsigned app binaries, APKs, installer bundles, and generated archives unless they are intentionally released with checksums.

## Safe To Publish

- Product overview and user setup instructions.
- Matrix/Synapse/Element-compatible architecture at a high level.
- Public security policy and abuse-reporting routes.
- Shield behaviour and licensing summaries.
- Roadmap items that do not reveal implementation details.
- Links to the live website, manuals, pricing, and official app/client setup.

## Pre-Publish Checks

1. Run a secret scan across tracked text files.
2. Review `README.md`, `SECURITY.md`, and `docs/` for implementation details that should stay private.
3. Confirm `.gitignore` excludes private folders, backups, logs, databases, credentials, and build outputs.
4. Confirm no generated account files or admin notes are staged.
5. Publish from `callchat/github-public`, not from the live service folder.
