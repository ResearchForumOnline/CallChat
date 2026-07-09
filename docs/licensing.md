# Licensing Notes

This is not legal advice. It is an engineering guide to avoid obvious mistakes.

## CallChat Community Code

Files written for this repository are MIT licensed unless a file says otherwise.

## Q Call Commercial License

The live Q Call secure-comms offer is sold separately from the MIT community kit:

- USD $55/month or USD $550/year.
- Unlimited users on one approved public server IP.
- Live buy/capture route: https://callchat.org/license/

The public repository can document pricing, buyer flow, and safe integration boundaries. A Q Call or Shield license does not automatically grant permission to republish private Shield/ZMath source, entitlement code, customer data, payment secrets, or production credentials.

## Upstream Software

Synapse, Element Web, Matrix SDKs, Docker images, and other dependencies keep their own licenses. Always read the license for the specific version you deploy.

## Safer Approach

- Configure upstream releases instead of copying or hiding them.
- Keep license files and notices.
- Link to upstream projects.
- Keep CallChat original code separate.
- Use permissive SDKs for original apps when possible.

## Risky Approach

- Distributing a modified closed-source fork of copyleft client code.
- Removing upstream notices.
- Mixing private commercial code directly into AGPL/copyleft code without review.
- Publishing private Shield/ZMath implementation by accident.
- Publishing payment provider secrets, webhook secrets, or customer lead data by accident.

## Practical Rule

If the plan is "take an upstream open-source app, deeply modify it, and ship it as closed-source CallChat," pause for licensing review first.
