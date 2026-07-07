# Update Policy

CallChat Community can feel stable without freezing security updates.

## Recommended Model

- Pin production versions.
- Keep a staging copy.
- Back up before every update.
- Test login, room join, media upload, and calls after updates.
- Apply security fixes promptly.
- Keep CallChat custom theme/config separate from upstream code.

## Do Not Do This

- Do not edit upstream Element Web source directly unless necessary.
- Do not remove license notices.
- Do not ignore security advisories.
- Do not change Synapse `server_name`.

## Release Notes

Keep a simple operator changelog:

- Date.
- Synapse version.
- Element Web version.
- Reverse proxy changes.
- TURN changes.
- Backup location.
- Rollback command.
