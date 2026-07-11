# Update Policy

CallChat Community can feel stable without freezing security updates.

## Recommended Model

- Pin production Synapse and Element versions. Do not run unattended `pip`,
  Git, archive-download, or container-tag upgrades for either application.
- Keep a staging copy.
- Back up before every update.
- Test login, room join, media upload, and calls after updates.
- Apply security fixes promptly.
- Keep CallChat custom theme/config separate from upstream code.

## Custom Production Lock

For a heavily customized deployment, separate application upgrades from OS
security maintenance:

- keep OS security updates enabled;
- keep the hosting panel's security lane enabled;
- disable automatic Synapse and Element application upgrades;
- record exact application versions and hashes in a root-owned manifest;
- alert on drift without automatically overwriting live files;
- require a reviewed release bundle, preflight tests, backup, and rollback for
  every intentional application change.

The lock is a deployment-control boundary, not a reason to ignore upstream
security advisories. A relevant security fix should be reviewed, integrated
with the CallChat custom layer, tested in staging, and released deliberately.

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
