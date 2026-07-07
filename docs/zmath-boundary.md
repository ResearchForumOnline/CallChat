# CallChat Shield Public Boundary

CallChat Shield is the optional premium layer for protected files and vault-style workflows.

## Publicly Safe To Say

- Standard Matrix-compatible messaging remains free.
- Shield is optional premium functionality.
- Shield-protected files can travel through Matrix as attachments.
- Clients without Shield support may download the protected file but will not provide the enhanced Shield workflow.
- A licensed deployment may expose Shield features to its own users.
- Public docs can describe outcomes, user experience, support model, and safe integration boundaries.

## Do Not Publish

- Private Shield/ZMath source.
- Implementation internals.
- Premium entitlement secrets.
- Premium policy source.
- Private research files.
- Test passwords or private credentials.
- Server signing keys.
- Database credentials.
- API keys.
- Access tokens.
- Recovery phrases.

## Security Wording

Use serious wording:

- "standard cryptographic controls"
- "user-owned secrets"
- "private implementation boundary"
- "optional premium vault layer"
- "PQC-ready roadmap" only where accurate

Avoid fake or unverifiable claims. Do not claim "quantum encryption" unless a real, reviewed mechanism exists and the limitation is explained clearly.

## Self-Hosted License

A self-hosted Shield license allows use on one licensed deployment. It does not grant permission to republish premium source unless a separate written license says so.

This repo can include stubs and docs that show where Shield hooks would appear, but it must not include the private implementation.
