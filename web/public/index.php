<?php
$brand = 'CallChat Community';
$matrixHost = 'matrix.example.com';
$publicHost = 'example.com';
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title><?php echo htmlspecialchars($brand); ?> - Matrix chat server kit</title>
  <meta name="description" content="Self-host a CallChat-style Matrix chat server with Synapse, PostgreSQL, Element Web configuration, voice/video notes, and a clean Shield boundary.">
  <link rel="stylesheet" href="/assets/style.css">
</head>
<body>
  <canvas id="matrixRain" aria-hidden="true"></canvas>
  <header class="site-header">
    <a class="brand" href="/">
      <img src="/assets/callchat-shield-z.svg" alt="">
      <span>
        <strong>CallChat</strong>
        <small>Matrix-compatible messenger</small>
      </span>
    </a>
    <nav aria-label="Main navigation">
      <a href="/connect/">Connect</a>
      <a href="/downloads/">Downloads</a>
      <a href="/#shield">Shield</a>
      <a href="https://github.com/ResearchForumOnline/CallChat" rel="noopener">GitHub</a>
      <a href="/privacy.php">Privacy</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <div>
        <p class="eyebrow">Self-hosted secure messaging</p>
        <h1>Run your own CallChat-style Matrix server.</h1>
        <p class="lead">Synapse, PostgreSQL, Element Web, voice/video guidance, and a branded public front door that stays compatible with the Matrix ecosystem.</p>
        <div class="actions">
          <a class="primary" href="/connect/">Connect with Element</a>
          <a href="/downloads/">Download setup files</a>
          <a href="https://github.com/ResearchForumOnline/CallChat" rel="noopener">Open GitHub repo</a>
          <a href="#shield">Shield boundary</a>
        </div>
      </div>
      <aside class="console-card" aria-label="Homeserver summary">
        <span class="status-dot"></span>
        <h2>Example homeserver</h2>
        <dl>
          <dt>Public domain</dt>
          <dd><?php echo htmlspecialchars($publicHost); ?></dd>
          <dt>Matrix API</dt>
          <dd><?php echo htmlspecialchars($matrixHost); ?></dd>
          <dt>Registration</dt>
          <dd>Invite or admin controlled</dd>
          <dt>Calls</dt>
          <dd>TURN recommended</dd>
        </dl>
      </aside>
    </section>

    <section class="grid">
      <article>
        <span>01</span>
        <h2>Free Matrix chat</h2>
        <p>Direct messages, group rooms, media upload, device verification, and Matrix client compatibility stay at the core.</p>
      </article>
      <article>
        <span>02</span>
        <h2>Element-ready</h2>
        <p>Use hosted Element Web or official Element mobile/desktop apps with the homeserver you control.</p>
      </article>
      <article>
        <span>03</span>
        <h2>Voice/video path</h2>
        <p>Plan TURN relay early so calls work across home routers, mobile networks, and stricter office networks.</p>
      </article>
      <article id="shield">
        <span>04</span>
        <h2>Shield boundary</h2>
        <p>Optional premium Shield behaviour can be described safely without publishing proprietary cryptographic implementation code.</p>
      </article>
    </section>
  </main>

  <script src="/assets/app.js"></script>
</body>
</html>
