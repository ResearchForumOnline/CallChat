# FAQ

## Is CallChat a new chat protocol?

No. CallChat Community uses Matrix compatibility so users can connect with existing clients.

## Can I use Element?

Yes. Element Web and official Element mobile/desktop clients are the recommended first clients.

## Is Shield included?

No. This public repo includes safe Shield behaviour docs only. Private Shield/ZMath implementation code is not included.

## Can I freeze updates forever?

You can pin versions, but production servers should still receive security updates after testing.

## Can I run this on one server?

Yes for small deployments. Put PostgreSQL privately on the same server or Docker network, expose only HTTPS, and plan backups.

## Do I need federation?

Not for a private MVP. Federation can be enabled later after moderation and abuse controls are ready.
