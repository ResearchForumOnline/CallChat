# Web UI Setup Builder

`installer/web-ui/index.php` is a small PHP setup builder for Apache/CWP-style hosting.

It does not install packages or run privileged commands. It generates:

- `.well-known/matrix/client`
- `.well-known/matrix/server`
- Element `config.json`
- Synapse `.env` starter values

Use it to help non-technical admins create the correct files, then copy the output into the deployment.

## Why It Is Limited

A public web installer that can run root commands is dangerous. The safer pattern is:

1. Use the web UI to generate config.
2. Review the output.
3. Run CLI commands over SSH as an admin.
4. Keep secrets out of the public webroot.
