# Licensing Notes

This is not legal advice. It is an engineering guide to avoid obvious mistakes.

## CallChat Community Code

Files written for this repository are MIT licensed unless a file says otherwise.

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

## Practical Rule

If the plan is "take an upstream open-source app, deeply modify it, and ship it as closed-source CallChat," pause for licensing review first.
