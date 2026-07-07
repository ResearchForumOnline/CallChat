# Voice and Video Calls

Matrix clients can support voice and video calls, but reliable calls need TURN.

## Why TURN Matters

Two users may sit behind routers, mobile networks, VPNs, or corporate firewalls. TURN gives the call a relay path when direct peer-to-peer media cannot connect.

## Production Checklist

- Run coturn on a stable public IP.
- Open UDP/TCP ports required by your TURN config.
- Use long random TURN shared secrets.
- Keep TURN credentials out of GitHub.
- Configure Synapse `turn_uris`.
- Test calls across different networks.

## Client Expectations

Call quality depends on:

- Browser/client support.
- Network NAT type.
- TURN availability.
- Device microphone/camera permissions.
- Server bandwidth.
