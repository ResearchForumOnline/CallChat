(function () {
  "use strict";

  const DEFAULT_PROFILE = {
    edition: "community",
    label: "Community",
    shield: "optional",
    home: "https://callchat.org/",
    account: "https://callchat.org/chat/",
    security: "https://callchat.org/shield/",
    calls: "https://callchat.org/quantum-calls/",
    help: "https://callchat.org/manuals/",
    source: "https://github.com/ResearchForumOnline/CallChat"
  };

  function safeUrl(value, fallback) {
    try {
      const url = new URL(value, location.origin);
      return ["https:", "http:"].includes(url.protocol) ? url.href : fallback;
    } catch {
      return fallback;
    }
  }

  async function profile() {
    try {
      const response = await fetch("client-profile.json", {credentials: "same-origin", cache: "no-store"});
      if (!response.ok) return DEFAULT_PROFILE;
      return {...DEFAULT_PROFILE, ...await response.json()};
    } catch {
      return DEFAULT_PROFILE;
    }
  }

  function icon(name) {
    const icons = {
      home: "⌂",
      security: "◆",
      calls: "◉",
      account: "●",
      help: "?",
      source: "<>"
    };
    return icons[name] || "•";
  }

  function command(name, label, href) {
    const link = document.createElement("a");
    link.className = "cc-command";
    link.href = safeUrl(href, "https://callchat.org/");
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.title = label;
    link.innerHTML = `<span aria-hidden="true">${icon(name)}</span><b>${label}</b>`;
    return link;
  }

  async function mount() {
    if (document.getElementById("callchat-command-bar")) return;
    const settings = await profile();
    const bar = document.createElement("header");
    bar.id = "callchat-command-bar";
    bar.setAttribute("aria-label", "CallChat controls");

    const brand = document.createElement("a");
    brand.className = "cc-brand";
    brand.href = safeUrl(settings.home, "https://callchat.org/");
    brand.target = "_blank";
    brand.rel = "noopener noreferrer";
    brand.innerHTML = `<img src="callchat-logo.svg" alt=""><span><strong>CallChat</strong><small>${String(settings.label).slice(0, 32)}</small></span>`;

    const commands = document.createElement("nav");
    commands.className = "cc-commands";
    commands.append(
      command("home", "Home", settings.home),
      command("security", "Shield", settings.security),
      command("calls", "Calls", settings.calls),
      command("account", "Account", settings.account),
      command("help", "Help", settings.help)
    );
    if (settings.edition === "community") commands.append(command("source", "Source", settings.source));

    const posture = document.createElement("div");
    posture.className = "cc-posture";
    posture.dataset.state = settings.shield === "included" ? "included" : "optional";
    posture.innerHTML = `<i></i><span>${settings.shield === "included" ? "ZMath included" : "Matrix secure"}</span>`;
    bar.append(brand, commands, posture);
    document.body.append(bar);
    document.documentElement.classList.add("callchat-client");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, {once: true});
  else mount();
})();
