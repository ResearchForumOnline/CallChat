# CLI Installer

`scripts/callchatctl.sh` is the public CallChat operator helper.

It is designed to be conservative:

- It writes config files only when asked.
- It backs up a webroot before widget injection.
- It does not commit secrets.
- It does not publish private Shield/ZMath code.
- It does not silently expose admin panels.

## Main Commands

```bash
bash install.sh
bash scripts/callchatctl.sh install-element
bash scripts/callchatctl.sh start-stack
bash scripts/callchatctl.sh install-openzero
bash scripts/callchatctl.sh install-widget /var/www/example.com/public
bash scripts/callchatctl.sh status https://example.com https://matrix.example.com
```

## What Gets Installed

- Synapse and PostgreSQL through Docker Compose.
- Element Web as static files downloaded from the Element Web release feed.
- CallChat theme/config files.
- Optional OpenZero through the public OpenZero installer.
- Optional widget assets into a chosen website root.

## What Does Not Get Installed

- Private Shield/ZMath implementation.
- Production signing keys.
- Production account passwords.
- Hidden premium entitlement code.

Those stay private by design.
