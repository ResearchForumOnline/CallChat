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

## Hosted CallChat Permission Flow

The hosted CallChat client keeps media permissions independent:

1. Joining requests microphone access.
2. The camera remains off until the user selects **Start video**.
3. Camera access is then requested separately.
4. Safari users may need to select **Enable sound** once when the browser
   pauses incoming audio under its autoplay policy.

Declining camera access does not disable the voice path. Screen sharing remains
a separate, explicit action and browser permission.
