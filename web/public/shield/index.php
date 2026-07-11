
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CallChat Shield - Local ZME1 Protection</title>
    <meta name="description" content="Protect messages, files, and vault notes locally as authenticated ZShield envelopes, then send only ciphertext through CallChat.">
    <link rel="canonical" href="https://callchat.org/shield/">
    <meta property="og:title" content="CallChat Shield">
    <meta property="og:description" content="Protect messages, files, and vault notes locally as authenticated ZShield envelopes, then send only ciphertext through CallChat.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://callchat.org/shield/">
    <meta name="twitter:card" content="summary">
    <meta name="theme-color" content="#030406">
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="CallChat">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="stylesheet" href="/assets/style.css?v=20260709-product2">
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "CallChat Shield",
        "applicationCategory": "SecurityApplication",
        "url": "https://callchat.org/shield/",
        "description": "Local authenticated ZShield protection for messages, files, and vault notes sent through CallChat.",
        "offers": [
          {"@type": "Offer", "name": "Hosted CallChat Shield", "price": "0", "priceCurrency": "USD"},
          {"@type": "Offer", "name": "Self-hosted ZMath Shield / Q Call Monthly", "price": "55", "priceCurrency": "USD"},
          {"@type": "Offer", "name": "Self-hosted ZMath Shield / Q Call Annual", "price": "550", "priceCurrency": "USD"}
        ]
      }
    </script>
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="/"><span class="brand-mark brand-logo-mark"><img src="/assets/images/zmath-shield-logo.svg" alt="" aria-hidden="true"></span><span><strong>CallChat ZERO</strong><small>Shield</small></span></a>
      <nav aria-label="Primary navigation">
        <a href="/">Home</a>
        <a href="/chat/">Web Chat</a>
        <a href="/connect/">Element</a>
        <a href="/manuals/">Manuals</a>
        <a href="/faq/">FAQ</a>
        <a href="/pricing/">Pricing</a>
        <a href="/license/">Buy</a>
        <a href="/guide/">PDF</a>
      </nav>
    </header>

    <main class="page-shell">
      <section class="page-hero">
        <p class="eyebrow">ZMath / Zero Boundary Algebra</p>
        <h1>Encrypt locally. Send the container.</h1>
        <p>
          ZShield turns a message, file, or vault note into an authenticated envelope inside your browser.
          The passphrase, optional pattern file, and plaintext stay on your device. Matrix E2EE protects the room;
          ZShield adds a separate encrypted payload you can paste, attach, and forward.
        </p>
        <div class="page-actions">
          <a class="button primary" href="/shield/app/">Open ZShield workspace</a>
          <a class="button secondary" href="/element/#/login">Open CallChat</a>
          <a class="button ghost" href="/license/">Founding pilot</a>
        </div>
      </section>

      <section class="product-band">
        <div>
          <p class="eyebrow">Working hosted MVP</p>
          <h2>The protected-message and file paths are live and testable.</h2>
          <p>
            The current workspace uses a deliberate passphrase and an optional pattern file, derives a local key,
            and applies AES-256-GCM authentication before download. Automatic account vault and recovery management
            remain a later reviewed milestone and are not claimed as active today.
          </p>
          <p>
            Standard Matrix chat remains free. Shield is additive: use the workspace to protect selected messages,
            vault notes, and attachments before placing the ciphertext in an encrypted Matrix room.
          </p>
        </div>
        <div class="status-list">
          <div><strong>Current rooms</strong><span>Live status confirms Matrix E2EE across every existing CallChat room.</span></div>
          <div><strong>ZShield payloads</strong><span>Messages, files, and vault notes can be protected locally as authenticated envelopes.</span></div>
          <div><strong>Element fallback</strong><span>Element can send, download, and forward the encrypted attachment.</span></div>
        </div>
      </section>

      <section class="content-card">
        <h2>How Shield is presented to users</h2>
        <div class="quick-steps">
          <article>
            <strong>01</strong>
            <span>Select content</span>
            <small>A chat message, file, attachment, or vault note is marked for Shield protection.</small>
          </article>
          <article>
            <strong>02</strong>
            <span>Protect locally</span>
            <small>The workspace derives the key and produces an authenticated container on your device.</small>
          </article>
          <article>
            <strong>03</strong>
            <span>Send or store</span>
            <small>A message envelope is pasted into Matrix, or a protected <code>.zme1</code> file travels as an attachment.</small>
          </article>
        </div>
        <p class="notice">
          The hosted MVP uses reviewable standard Web Crypto primitives. Premium entitlement, managed recovery,
          enterprise policy, and managed recovery remain separate from this security baseline. Owners can optionally
          add a separately held IonQ hardware-linked factor that is required by the selected ZShield KDF profile.
          It is not QKD or a claim that IonQ performs encryption.
        </p>
      </section>

      <section class="pricing-grid" aria-label="Shield licensing summary">
        <article class="license-card">
          <span>Hosted</span>
          <h2>CallChat</h2>
          <p>Free hosted workspace for protecting and opening ZME1 files and vault notes locally.</p>
          <strong>$0</strong>
          <a class="button secondary" href="/connect/">Start with CallChat</a>
        </article>
        <article class="license-card featured">
          <span>Self-hosted</span>
          <h2>Founding Pilot</h2>
          <p>Monthly pilot for one approved server: deployment review, protected-file setup, Q-Call posture, and direct onboarding.</p>
          <strong>$55/month</strong>
          <a class="button primary" href="/license/#buy">Buy monthly</a>
        </article>
        <article class="license-card">
          <span>Annual</span>
          <h2>Annual Pilot</h2>
          <p>The same founding deployment scope on an annual schedule, including review checkpoints as the product matures.</p>
          <strong>$550/year</strong>
          <a class="button secondary" href="/license/#buy">Buy yearly</a>
        </article>
        <article class="license-card">
          <span>Self-hosted</span>
          <h2>Server License</h2>
          <p>Use the proprietary Shield layer on one approved CallChat-compatible deployment while premium source stays protected.</p>
          <strong>Unlimited users</strong>
          <a class="button secondary" href="/license/#buy">Get license</a>
        </article>
      </section>

      <section class="content-card">
        <h2>What license buyers get</h2>
        <div class="resource-grid">
          <article class="mini-card">
            <h3>Working local flow</h3>
            <p>Users can protect and open files today with a clear authenticated-encryption workflow.</p>
          </article>
          <article class="mini-card">
            <h3>Policy entitlement</h3>
            <p>Licensed servers can use approved entitlement checks for self-hosted Shield and Q Call access.</p>
          </article>
          <article class="mini-card">
            <h3>Protected source boundary</h3>
            <p>Licensing grants use of the premium layer, not republication of private ZMath source code.</p>
          </article>
          <article class="mini-card">
            <h3>Clear fallback</h3>
            <p>Normal Matrix messaging remains usable; Shield files appear as protected containers to clients without Shield tooling.</p>
          </article>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <a href="/chat/">Web Chat</a>
      <a href="/manuals/">Manuals</a>
      <a href="/faq/">FAQ</a>
      <a href="/pricing/">Pricing</a>
      <a href="/license/">Buy</a>
      <a href="/guide/">Guide</a>
      <a href="/terms/">Terms</a>
      <a href="/privacy/">Privacy</a>
    </footer>
    <script src="/assets/zero-live-agent.js?v=20260709-product2" defer></script>
  </body>
</html>
