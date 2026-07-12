# Mobile ZMath Profile Recovery

CallChat's hosted Shield client can restore a trusted ZMath profile on a new phone
or browser using the same shared passphrase and exact pattern image. The trusted
copy is scoped to the signed-in Matrix account and must lock on logout or account
switch.

## User Flow

1. Open the hosted CallChat client in a current mobile browser.
2. Sign in to the intended CallChat account.
3. Complete Matrix device verification or key recovery if prompted.
4. Import the shared ZMath passphrase and exact pattern image.
5. Run the authenticated self-test before relying on the restored profile.

Matrix device trust and the optional ZMath profile are separate layers. Restoring
one does not bypass the other.

## Browser Requirements

The hosted flow requires HTTPS, WebCrypto, and IndexedDB. Current Brave, Chrome,
Firefox, and Safari releases provide these capabilities. Private browsing or site
data cleanup may remove the trusted local copy and require another import.

This document describes product behavior only. It intentionally excludes private
ZMath source, cryptographic internals, credentials, recovery material, and
production account information.
