# Public Security and IP Boundary Update

Date: 12 July 2026

This release tightens the separation between CallChat Community and the licensed Shield/ZMath product.

## Public changes

- Keeps the Matrix-compatible community deployment kit, registration service, bot examples, website templates, and non-secret provider controls public.
- Removes premium Shield/ZMath browser implementation source, development tests, test vectors, and implementation-level design notes from the current distribution.
- Adds an automated disclosure-boundary check to prevent those private module paths from being recommitted.
- Clarifies that the repository MIT license covers only files distributed in the community repository.
- Retains honest product and security boundaries without publishing recovery logic, policy internals, entitlement code, production configuration, credentials, or private research.

## Open-source client boundary

The modified Element Web and Element Call clients are governed by their AGPL/GPL or commercial-license terms. Their required corresponding source remains public. Integration hooks and media-client modifications published there are therefore open implementation, not confidential IP. Private commercial work must be kept in separately designed modules after a licensing review.

## Hosted production hardening

The hosted service separately blocks source maps, browser test modules, test vectors, hidden files, and development artifacts. Required production assets remain available with no-index and same-origin controls.

## Security language

CallChat does not claim that current calls are quantum encrypted. MatrixRTC and LiveKit provide the deployed call-media foundation. Optional quantum-service work is described only at the capability and provider boundary; implementation details remain in the licensed/private lane.

Previously published Git history may still contain earlier revisions. Removing files from the current tree does not erase third-party copies or revoke rights already granted to copies distributed under their original license. Future proprietary modules must remain outside the public repository from inception.
