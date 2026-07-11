# CallChat Community Web Client

CallChat Community is the public client layer used to produce the branded
CallChat web experience while retaining Matrix protocol compatibility.

The distribution is assembled from Element Web `v1.12.23` plus the files in
this directory. Element Web is licensed under AGPL-3.0 (or a separate commercial
licence from Element). CallChat Community modifications are published so hosted
users can obtain the corresponding source required by the AGPL network-use
clause.

## Editions

- **Community** uses this complete public client and can connect to any approved
  Matrix homeserver configured by its operator.
- **Shield Showcase** uses the same public client at `callchat.org/app/` with
  CallChat's server-side entitlement, policy, support, managed recovery and
  customer operations. Those separate services are not hidden modifications to
  the AGPL client.
- **Element compatibility** remains available at `callchat.org/element/` and in
  the official mobile/desktop apps.

## Public files

- `config.community.json` - safe self-host template.
- `client-profile.community.json` - edition and navigation profile.
- `callchat-shell.js` / `callchat-shell.css` - branded command surface.
- `home.html` - embedded CallChat workspace.
- `callchat-client.test.mjs` - distribution contract.

Do not commit production credentials, customer records, entitlement secrets,
server access details or private ZMath research here.
