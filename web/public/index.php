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
  <title><?php echo htmlspecialchars($brand); ?> - Q Call secure comms</title>
  <meta name="description" content="Get Q Call secure comms for USD 55/month or USD 550/year, with self-hosted Matrix chat, calls, Element Web configuration, OpenZero agent support, and a clean Shield boundary.">
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
      <a href="/license/">Q Call License</a>
      <a href="/#shield">Shield</a>
      <a href="https://github.com/ResearchForumOnline/CallChat" rel="noopener">GitHub</a>
      <a href="/privacy.php">Privacy</a>
    </nav>
  </header>

  <main>
    <section class="hero">
      <div>
        <p class="eyebrow">Secure comms with Q Call</p>
        <h1>Get privacy and protection in the quantum age.</h1>
        <p class="lead">Q Call gives teams a self-hosted CallChat route for messages, rooms, calls, and protected workflows. Licenses are USD 55/month or USD 550/year for unlimited users on one approved public server IP.</p>
        <div class="actions">
          <a class="primary" href="/license/">Get your license now</a>
          <a href="https://callchat.org/license/#buy" rel="noopener">Buy on callchat.org</a>
          <a href="/connect/">Connect with Element</a>
          <a href="/downloads/">Download setup files</a>
          <a href="https://github.com/ResearchForumOnline/CallChat" rel="noopener">Open GitHub repo</a>
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
          <dt>Q Call license</dt>
          <dd>USD 55/mo or USD 550/yr</dd>
        </dl>
      </aside>
    </section>

    <section class="grid">
      <article>
        <span>01</span>
        <h2>Know</h2>
        <p>Self-host messages, rooms, media, and calls on a Matrix-compatible foundation with a CallChat front door.</p>
      </article>
      <article>
        <span>02</span>
        <h2>Like</h2>
        <p>Simple pricing, unlimited users on one approved public server IP, and a practical route for teams that want control.</p>
      </article>
      <article>
        <span>03</span>
        <h2>Trust</h2>
        <p>Security language stays serious: quantum-ready roadmap, private Shield boundary, and no impossible promises.</p>
      </article>
      <article id="shield">
        <span>04</span>
        <h2>Buy</h2>
        <p>Use the live capture page to request setup help or buy the Q Call secure-comms license.</p>
        <p><a href="https://callchat.org/license/#buy" rel="noopener">Open buy page</a></p>
      </article>
    </section>
  </main>

  <script src="/assets/app.js"></script>
</body>
</html>
