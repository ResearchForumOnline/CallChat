# AGENTS.md

Rules for Codex, maintainers, and automation working in this repository.

## Scope

This public repo is the CallChat Community self-host kit. It may contain website templates, Synapse/PostgreSQL templates, Element Web configuration, docs, and safe integration examples.

It must not contain private ZMath/CallChat Shield implementation code or production secrets.

## Safety Rules

- Back up before modifying live server configs.
- No destructive changes without explicit approval.
- No production deploy without a rollback plan.
- No secrets in git.
- No printing secrets to logs.
- Do not touch files outside this repository unless the owner approves.
- Keep public website PHP/JS compatible with Apache/CWP.
- Synapse/PostgreSQL may run as Docker/KVM services.
- Preserve Matrix and Element compatibility.
- Keep CallChat branding/config separate from upstream code.
- ZMath/CallChat Shield proprietary code belongs in private modules only.
- Avoid AGPL/copyleft contamination unless the project intentionally complies.
- Do not fork Element X or Element Web into a closed-source commercial app without licensing review.
- Prefer permissive libraries for original CallChat app code where possible.
- Security must rely on strong cryptography and keys, not secret algorithms alone.
- Assume mobile and browser code can be reverse engineered.
- Public browser JavaScript must not contain proprietary premium encryption secrets.
- Every task should end with changed files, tests run, and the next safe step.

## Release Boundary

Allowed:

- Public docs.
- Install scripts.
- Example config files using placeholders.
- Website templates.
- Element Web configuration examples.
- AI bot integration docs/templates without tokens.

Not allowed:

- Real `.env` values.
- Matrix signing keys.
- Synapse registration secrets.
- Database passwords.
- Access tokens.
- SSH keys.
- Private Shield/ZMath source.
- Production account lists.
- Backups or dumps.
