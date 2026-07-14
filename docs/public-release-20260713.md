# Hosted Reliability and Mobile Release

Date: 13 July 2026

This hosted release improves CallChat's mobile experience, AI-room reliability,
production integrity controls, and recoverability. It does not publish licensed
Shield/ZMath implementation details or production configuration.

## Customer-visible improvements

- Moves account creation into the first mobile viewport and improves the
  account, payment-return, and Shield panel layouts on narrow screens.
- Adds accessible tab, dialog, status, focus, and keyboard behaviour to the
  hosted account and protection controls.
- Keeps the protection preference bound to the signed-in account and fails
  closed when the account changes.
- Validates recovery images before local use and blocks unsupported attachment
  paths that could otherwise bypass the intended protected-file flow.
- Clarifies call status so the interface distinguishes a ready call service from
  media protection negotiated after a participant joins.

## Bot and local-AI reliability

- Restricts the special bot-room path to a verified Matrix room identity rather
  than a visible room name.
- Prevents ordinary room conversation from entering the AI prompt context.
- Keeps secret-like prompts out of retained bot context.
- Reports whether a reply came from OpenZero or from the bounded product-answer
  fallback instead of labelling both routes as model output.
- Connects the hosted bot bridge to its owner-controlled model service through
  an encrypted private transport and keeps the model API off the public network.

## Hosted operations

- Serves the customized browser release from a root-owned, non-writable release
  tree with a complete integrity manifest and automated drift checks.
- Pins the hosted application release while preserving deliberate, tested
  security-update and rollback procedures.
- Retains two low-priority recovery copies on dedicated storage. Each copy
  includes the hosted site, Matrix database and media, and required service
  configuration, with checksums and archive/catalog validation.
- Restricts authenticated TURN relays from reaching private, loopback,
  link-local, reserved, or multicast peer networks.

## Commercial clarity

- Aligns the pricing, licence, terms, payment-return, and site-agent language
  around the founding Q Call / Shield deployment offer.
- Explains activation timing, approved-server scope, setup review, support
  boundaries, cancellation, invoicing, migration, and account-recovery limits.
- Treats the PayPal return page as a customer status step, not proof of payment.

## Public boundary

The community repository continues to publish deployment guidance, safe
integration examples, customer-facing capability boundaries, and required
open-source client materials. It does not publish production credentials,
server topology, private recovery logic, entitlement code, licensed Shield/ZMath
modules, or proprietary research.

Current Q Calls use the deployed MatrixRTC/LiveKit WebRTC media stack. CallChat
does not claim that live audio or video is quantum encrypted. Optional quantum
provider work remains outside the live media-key path and must be described by
its verified function rather than as QKD.
