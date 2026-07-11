# CallChat Capability Boundary

This page separates deployed capabilities from product roadmap language. It is
the reference for website copy, demonstrations, sales material, and status
badges.

## Available now

- Matrix-compatible rooms and encrypted messaging.
- Voice and video through WebRTC with DTLS-SRTP and configured TURN support.
- A CallChat-branded web client based on maintained Element Web source.
- Local ZME1 message and file protection using the documented Web Crypto
  profile: PBKDF2-SHA-256 and AES-256-GCM.
- ZMath Auto integration that protects selected composer text and attachments
  locally after the user unlocks it with the required factors.
- An optional IonQ hardware-linked `.zqf` factor that is mixed into ZShield
  content keys and the ZMath call media root. Missing or incorrect factors fail
  closed; simulator output cannot activate the hardware profile.
- CAPTCHA-protected Matrix registration, a restricted E2EE Matrix bot example,
  public status schemas, and self-hosting templates.

## Commercial deployment scope

The USD 55 monthly or USD 550 annual offer covers one approved public server IP
with unlimited users on that deployment. It is a self-hosted Shield/Q Call
license and onboarding route, not ownership of private ZMath research or source.
The exact entitlement and support terms on the live checkout page control.

## Research and roadmap

- Standardized post-quantum key establishment and signature integration.
- Cryptographic agility and migration policy for future protocol upgrades.
- Standardized ML-KEM key establishment and hybrid protocol integration.
- Further managed recovery, enterprise policy, and deployment automation.

Roadmap items are not presented as deployed cryptographic protection.

## Claims CallChat does not make

- Current voice or video packets are quantum encrypted.
- The IonQ integration is quantum key distribution, quantum cryptography, or a
  certified quantum random-number generator.
- IonQ receives or stores the local nonce, final `.zqf` factor, or user keys.
- Any encryption system is unbreakable, quantum-proof forever, or a substitute
  for independent security review.
- A sample interface badge proves the state of a real account or device.
- Matrix transport alone applies the private ZMath layer automatically in every
  compatible third-party client.

## Demonstration rule

Interface mockups must be labelled as illustrative. Live status should come
from an authenticated client state or a documented status endpoint, and a
failed check must be shown as unavailable rather than silently replaced with a
success badge.
