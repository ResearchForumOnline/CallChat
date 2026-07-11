# Layered file protection

CallChat does not replace Matrix encryption. When ZMath protection is enabled,
it protects the original file locally first, then hands the protected container
to the normal Matrix encrypted-file path.

```text
Original document
        |
        v
ZMath user factors
(passphrase + exact pattern)
        |
        v
Authenticated AES-256-GCM ZME1 container
filename.docx.zme1
        |
        v
Matrix A256CTR encrypted attachment
        |
        v
Megolm-encrypted room event
        |
        v
CallChat infrastructure receives encrypted payloads
```

## What the layers do

1. The CallChat client uses the user's ZMath factors to create an authenticated
   `.zme1` container before upload.
2. Matrix encrypts that container as an attachment. In the current Matrix file
   event format, this attachment layer is identified as `A256CTR`.
3. The attachment reference and file details are carried inside a
   Megolm-encrypted room event.
4. The CallChat homeserver and media service receive the Matrix-encrypted
   payload rather than the original document bytes in this protected path.

Successful recovery requires the Matrix room encryption context and the exact
ZMath factors used for the ZME1 container. Changing the authenticated container
causes ZME1 verification to fail instead of returning modified plaintext.

## Security boundary

- The extra ZME1 layer applies only when ZMath protection is enabled and
  unlocked. Matrix-only mode does not create this additional container.
- The passphrase, pattern, and recovered plaintext are intended to stay in the
  client-side protection flow.
- Service infrastructure may still process operational metadata required to
  deliver the service, including account and room routing, timestamps, traffic
  timing, and encrypted payload sizes.
- This document names the public protection layers. Private ZMath research,
  premium policy, credentials, recovery systems, and deployment secrets are not
  published here.

This design uses established classical cryptographic layers. It does not by
itself constitute a post-quantum encryption claim.
