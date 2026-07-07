(function () {
  const canvas = document.getElementById('matrixRain');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const chars = '0+-ZCALLCHAT';
  let width = 0;
  let height = 0;
  let drops = [];

  function resize() {
    width = canvas.width = window.innerWidth * window.devicePixelRatio;
    height = canvas.height = window.innerHeight * window.devicePixelRatio;
    const cols = Math.max(16, Math.floor(width / 28));
    drops = Array.from({ length: cols }, () => Math.random() * height);
  }

  function draw() {
    ctx.fillStyle = 'rgba(3, 8, 11, 0.08)';
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = 'rgba(56, 230, 255, 0.7)';
    ctx.font = `${16 * window.devicePixelRatio}px monospace`;

    drops.forEach((y, i) => {
      const text = chars[Math.floor(Math.random() * chars.length)];
      const x = i * 28 * window.devicePixelRatio;
      ctx.fillText(text, x, y);
      drops[i] = y > height && Math.random() > 0.975 ? 0 : y + 18 * window.devicePixelRatio;
    });

    requestAnimationFrame(draw);
  }

  resize();
  draw();
  window.addEventListener('resize', resize);
})();
