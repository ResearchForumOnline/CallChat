import {
  MESSAGE_PREFIX,
  PROFILE,
  containerFingerprint,
  openContainerPayload,
  openMessage,
  protectMessage,
  protectPayload
} from "/shield/app/zshield-core.js";

const VAULT_KEY = "callchat.zmath.auto.v1";
const MODE_KEY = "callchat.zmath.mode.v1";
const VAULT_ITERATIONS = 600000;
const MAX_AUTO_FILE_BYTES = 50 * 1024 * 1024;
const encoder = new TextEncoder();

let sessionPassphrase = "";
let sessionPattern = null;
let sessionPatternName = "";
let pendingPattern = null;
let pendingPatternName = "";
let bypassSend = false;
let bypassFile = false;
let busy = false;
let scanQueued = false;
const openedBodies = new Map();

function bytesToBase64(bytes) {
  let value = "";
  const chunk = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunk) {
    value += String.fromCharCode(...bytes.subarray(offset, offset + chunk));
  }
  return btoa(value);
}

function base64ToBytes(value) {
  const binary = atob(String(value || ""));
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

function randomBytes(length) {
  const output = new Uint8Array(length);
  crypto.getRandomValues(output);
  return output;
}

function isUnlocked() {
  return Boolean(sessionPassphrase && sessionPattern && sessionPattern.length);
}

function isMatrixOnly() {
  return localStorage.getItem(MODE_KEY) === "matrix";
}

function setMatrixOnly(enabled) {
  localStorage.setItem(MODE_KEY, enabled ? "matrix" : "shield");
  updateUi();
}

async function vaultKey(passphrase, salt) {
  const input = await crypto.subtle.importKey("raw", encoder.encode(passphrase), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey(
    {name: "PBKDF2", hash: "SHA-256", salt, iterations: VAULT_ITERATIONS},
    input,
    {name: "AES-GCM", length: 256},
    false,
    ["encrypt", "decrypt"]
  );
}

async function rememberPattern(passphrase, patternBytes, name) {
  const salt = randomBytes(16);
  const iv = randomBytes(12);
  const key = await vaultKey(passphrase, salt);
  const ciphertext = new Uint8Array(await crypto.subtle.encrypt(
    {name: "AES-GCM", iv, additionalData: encoder.encode("CallChat-ZMath-Device-Vault-1")},
    key,
    patternBytes
  ));
  localStorage.setItem(VAULT_KEY, JSON.stringify({
    version: 1,
    iterations: VAULT_ITERATIONS,
    salt: bytesToBase64(salt),
    iv: bytesToBase64(iv),
    ciphertext: bytesToBase64(ciphertext),
    name: String(name || "callchat-pattern.png").slice(0, 128)
  }));
}

async function loadRememberedPattern(passphrase) {
  const record = JSON.parse(localStorage.getItem(VAULT_KEY) || "null");
  if (
    !record ||
    record.version !== 1 ||
    record.iterations !== VAULT_ITERATIONS ||
    base64ToBytes(record.salt).length !== 16 ||
    base64ToBytes(record.iv).length !== 12
  ) {
    return null;
  }
  try {
    const key = await vaultKey(passphrase, base64ToBytes(record.salt));
    const plaintext = new Uint8Array(await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: base64ToBytes(record.iv),
        additionalData: encoder.encode("CallChat-ZMath-Device-Vault-1")
      },
      key,
      base64ToBytes(record.ciphertext)
    ));
    return {bytes: plaintext, name: record.name};
  } catch {
    throw new Error("Unlock failed. Check the passphrase or import the exact pattern image.");
  }
}

async function patternFingerprint(bytes) {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return Array.from(digest.subarray(0, 8), (value) => value.toString(16).padStart(2, "0")).join("");
}

function downloadBytes(bytes, name, type) {
  const url = URL.createObjectURL(new Blob([bytes], {type}));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.hidden = true;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}

async function generatePatternImage() {
  const seed = randomBytes(64);
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const context = canvas.getContext("2d", {alpha: false});
  context.fillStyle = "#071116";
  context.fillRect(0, 0, 256, 256);
  for (let index = 0; index < 64; index += 1) {
    const x = (index % 8) * 32;
    const y = Math.floor(index / 8) * 32;
    const value = seed[index];
    context.fillStyle = `hsl(${(value * 11) % 360} 72% ${36 + (value % 25)}%)`;
    context.fillRect(x + 3, y + 3, 26, 26);
    if (value & 1) {
      context.fillStyle = "#edf8f7";
      context.fillRect(x + 12, y + 12, 8, 8);
    }
  }
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  if (!blob) throw new Error("Pattern image generation failed.");
  pendingPattern = new Uint8Array(await blob.arrayBuffer());
  pendingPatternName = `callchat-zmath-pattern-${Date.now()}.png`;
  downloadBytes(pendingPattern, pendingPatternName, "image/png");
  updatePatternMeta();
  toast("Pattern image generated and downloaded. Keep it with your recovery material.");
  return {bytes: pendingPattern, name: pendingPatternName};
}

function generatePassphrase() {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const bytes = randomBytes(24);
  const groups = [];
  for (let group = 0; group < 6; group += 1) {
    let value = "";
    for (let index = 0; index < 4; index += 1) {
      value += alphabet[bytes[group * 4 + index] % alphabet.length];
    }
    groups.push(value);
  }
  return groups.join("-");
}

async function createAutomaticSetup() {
  const passphrase = generatePassphrase();
  document.getElementById("zmath-auto-passphrase").value = passphrase;
  await generatePatternImage();
  const recovery = document.getElementById("zmath-auto-recovery");
  const recoveryCode = document.getElementById("zmath-auto-recovery-code");
  recovery.hidden = false;
  recoveryCode.textContent = passphrase;
  await unlock();
  toast("ZMath Auto is active. Save the one-time passphrase separately from the downloaded pattern image.");
}

function createUi() {
  if (document.getElementById("zmath-auto-launcher")) return;
  const launcher = document.createElement("button");
  launcher.id = "zmath-auto-launcher";
  launcher.type = "button";
  launcher.textContent = "ZMath locked";
  launcher.title = "Open ZMath Auto";

  const panel = document.createElement("section");
  panel.id = "zmath-auto-panel";
  panel.hidden = true;
  panel.setAttribute("aria-label", "ZMath Auto settings");
  panel.innerHTML = `
    <div class="zmath-auto-head">
      <strong>ZMath Auto</strong>
      <button class="zmath-auto-close" type="button" aria-label="Close">×</button>
    </div>
    <div class="zmath-auto-body">
      <p class="zmath-auto-state" id="zmath-auto-state"></p>
      <button class="zmath-auto-primary zmath-auto-setup" id="zmath-auto-setup" type="button">Create secure setup automatically</button>
      <div class="zmath-auto-recovery" id="zmath-auto-recovery" hidden>
        <strong>Save this passphrase now</strong>
        <code id="zmath-auto-recovery-code"></code>
        <button id="zmath-auto-copy-recovery" type="button">Copy passphrase</button>
        <small>It is shown once and is not stored. Keep it separately from the downloaded pattern image.</small>
      </div>
      <label class="zmath-auto-field">
        <span>Passphrase</span>
        <input id="zmath-auto-passphrase" type="password" minlength="14" autocomplete="current-password">
      </label>
      <div class="zmath-auto-actions">
        <button id="zmath-auto-generate-pass" type="button">Generate passphrase</button>
        <button id="zmath-auto-generate-pattern" type="button">Generate pattern image</button>
      </div>
      <label class="zmath-auto-field">
        <span>Exact pattern image</span>
        <input id="zmath-auto-pattern" type="file" accept="image/*">
      </label>
      <p class="zmath-auto-meta" id="zmath-auto-pattern-meta">No pattern loaded.</p>
      <div class="zmath-auto-row">
        <label><input id="zmath-auto-remember" type="checkbox" checked> Remember image encrypted on this device</label>
      </div>
      <div class="zmath-auto-row">
        <label><input id="zmath-auto-matrix-only" type="checkbox"> Matrix-only sending</label>
      </div>
      <div class="zmath-auto-actions">
        <button class="zmath-auto-primary" id="zmath-auto-unlock" type="button">Unlock ZMath</button>
        <button id="zmath-auto-lock" type="button">Lock</button>
        <button class="zmath-auto-danger" id="zmath-auto-forget" type="button">Forget device image</button>
      </div>
      <div class="zmath-auto-diagnostic">
        <button id="zmath-auto-self-test" type="button">Run encryption self-test</button>
        <p id="zmath-auto-self-test-result">Not run in this session.</p>
      </div>
      <p class="zmath-auto-meta">Profile: <span id="zmath-auto-profile"></span></p>
    </div>`;
  const toastElement = document.createElement("div");
  toastElement.id = "zmath-auto-toast";
  toastElement.hidden = true;
  toastElement.setAttribute("role", "status");
  document.body.append(launcher, panel, toastElement);

  launcher.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    if (!panel.hidden) document.getElementById("zmath-auto-passphrase").focus();
  });
  panel.querySelector(".zmath-auto-close").addEventListener("click", () => {
    panel.hidden = true;
  });
  document.getElementById("zmath-auto-setup").addEventListener("click", () => {
    createAutomaticSetup().catch(showError);
  });
  document.getElementById("zmath-auto-copy-recovery").addEventListener("click", async () => {
    const value = document.getElementById("zmath-auto-recovery-code").textContent || "";
    if (!value) return;
    await navigator.clipboard.writeText(value);
    toast("Passphrase copied. Store it separately from the pattern image.");
  });
  document.getElementById("zmath-auto-generate-pass").addEventListener("click", () => {
    const passphrase = generatePassphrase();
    document.getElementById("zmath-auto-passphrase").value = passphrase;
    toast("A strong passphrase was generated. Record it separately from the pattern image.");
  });
  document.getElementById("zmath-auto-generate-pattern").addEventListener("click", () => {
    generatePatternImage().catch(showError);
  });
  document.getElementById("zmath-auto-pattern").addEventListener("change", async (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    pendingPattern = new Uint8Array(await file.arrayBuffer());
    pendingPatternName = file.name;
    updatePatternMeta();
  });
  document.getElementById("zmath-auto-unlock").addEventListener("click", () => {
    unlock().catch(showError);
  });
  document.getElementById("zmath-auto-lock").addEventListener("click", lock);
  document.getElementById("zmath-auto-forget").addEventListener("click", () => {
    localStorage.removeItem(VAULT_KEY);
    pendingPattern = null;
    pendingPatternName = "";
    lock();
    updatePatternMeta();
    toast("Encrypted device image removed.");
  });
  document.getElementById("zmath-auto-self-test").addEventListener("click", () => {
    runSelfTest().catch(showError);
  });
  document.getElementById("zmath-auto-matrix-only").addEventListener("change", (event) => {
    setMatrixOnly(event.target.checked);
  });
  document.getElementById("zmath-auto-profile").textContent = PROFILE;
  updateUi();
}

async function updatePatternMeta() {
  const element = document.getElementById("zmath-auto-pattern-meta");
  if (!element) return;
  const bytes = pendingPattern || sessionPattern;
  const name = pendingPatternName || sessionPatternName;
  if (!bytes || !bytes.length) {
    element.textContent = localStorage.getItem(VAULT_KEY)
      ? "Encrypted device image is available."
      : "No pattern loaded.";
    return;
  }
  element.textContent = `${name} · fingerprint ${await patternFingerprint(bytes)}`;
}

function updateUi() {
  const launcher = document.getElementById("zmath-auto-launcher");
  const state = document.getElementById("zmath-auto-state");
  const matrixOnly = isMatrixOnly();
  if (!launcher || !state) return;
  document.getElementById("zmath-auto-matrix-only").checked = matrixOnly;
  if (matrixOnly) {
    launcher.textContent = "Matrix only";
    launcher.dataset.state = "matrix";
    state.textContent = "ZMath interception is off. Matrix E2EE continues normally.";
    state.dataset.state = "matrix";
  } else if (isUnlocked()) {
    launcher.textContent = "ZMath auto";
    launcher.dataset.state = "ready";
    state.textContent = "Unlocked. Messages and selected attachments are protected locally before Element sends them.";
    state.dataset.state = "ready";
  } else {
    launcher.textContent = "ZMath locked";
    launcher.dataset.state = "locked";
    state.textContent = "Unlock before sending. Incoming ZMath content opens only while this browser session is unlocked.";
    state.dataset.state = "locked";
  }
  updatePatternMeta();
}

async function unlock() {
  const passphrase = document.getElementById("zmath-auto-passphrase").value;
  if (passphrase.length < 14) throw new Error("Use a passphrase with at least 14 characters.");
  let pattern = pendingPattern;
  let name = pendingPatternName;
  if (!pattern) {
    const remembered = await loadRememberedPattern(passphrase);
    if (remembered) {
      pattern = remembered.bytes;
      name = remembered.name;
    }
  }
  if (!pattern || !pattern.length) throw new Error("Import or generate the exact pattern image first.");
  sessionPassphrase = passphrase;
  sessionPattern = pattern.slice();
  sessionPatternName = name;
  pendingPattern = null;
  pendingPatternName = "";
  if (document.getElementById("zmath-auto-remember").checked) {
    await rememberPattern(passphrase, sessionPattern, sessionPatternName);
  }
  document.getElementById("zmath-auto-passphrase").value = "";
  setMatrixOnly(false);
  updateUi();
  queueIncomingScan();
  toast("ZMath Auto unlocked for this browser session.");
}

function lock() {
  sessionPassphrase = "";
  if (sessionPattern) sessionPattern.fill(0);
  sessionPattern = null;
  sessionPatternName = "";
  for (const [body, opened] of openedBodies) {
    body.hidden = false;
    opened.remove();
  }
  openedBodies.clear();
  updateUi();
}

function showError(error) {
  toast(error instanceof Error ? error.message : "ZMath operation failed.");
}

async function runSelfTest() {
  if (!isUnlocked()) throw new Error("Unlock ZMath before running the encryption self-test.");
  const plaintext = randomBytes(1024);
  const container = await protectPayload({
    bytes: plaintext,
    name: "callchat-zmath-self-test.bin",
    type: "application/octet-stream",
    kind: "diagnostic",
    passphrase: sessionPassphrase,
    patternBytes: sessionPattern,
    context: {
      purpose: "local-self-test",
      zmathPolicy: "ZMath-Auto-Policy-2",
      transport: "local-only"
    }
  });
  const opened = await openContainerPayload({
    container,
    passphrase: sessionPassphrase,
    patternBytes: sessionPattern
  });
  const matches = opened.bytes.length === plaintext.length && opened.bytes.every((byte, index) => byte === plaintext[index]);
  plaintext.fill(0);
  opened.bytes.fill(0);
  if (!matches) throw new Error("ZMath self-test failed. Do not send protected content from this session.");
  const fingerprint = await containerFingerprint(container);
  const result = document.getElementById("zmath-auto-self-test-result");
  result.textContent = `Passed · authenticated 1 KB round-trip · ${fingerprint}`;
  result.dataset.state = "passed";
  toast("ZMath self-test passed. Encryption, authentication and local decryption are working.");
}

let toastTimer;
function toast(message) {
  const element = document.getElementById("zmath-auto-toast");
  if (!element) return;
  element.textContent = String(message);
  element.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    element.hidden = true;
  }, 5200);
}

function composerFor(target) {
  return target instanceof Element ? target.closest(".mx_MessageComposer") : null;
}

function editorFor(composer) {
  return composer && (
    composer.querySelector('[contenteditable="true"][role="textbox"]') ||
    composer.querySelector('[contenteditable="true"]') ||
    composer.querySelector("textarea")
  );
}

function editorText(editor) {
  return editor instanceof HTMLTextAreaElement ? editor.value : editor.innerText;
}

function writeEditor(editor, value) {
  editor.focus();
  if (editor instanceof HTMLTextAreaElement) {
    editor.value = value;
  } else {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(editor);
    selection.removeAllRanges();
    selection.addRange(range);
    if (!document.execCommand("insertText", false, value)) {
      editor.textContent = value;
    }
  }
  editor.dispatchEvent(new InputEvent("input", {
    bubbles: true,
    inputType: "insertText",
    data: value
  }));
}

async function protectComposerAndSend(composer) {
  if (busy) return;
  const editor = editorFor(composer);
  const message = editor && editorText(editor).trim();
  if (!message || message.startsWith(MESSAGE_PREFIX)) return;
  if (!isUnlocked()) {
    document.getElementById("zmath-auto-panel").hidden = false;
    toast("Unlock ZMath before sending, or explicitly choose Matrix-only sending.");
    return;
  }
  busy = true;
  composer.classList.add("zmath-auto-busy");
  try {
    const protectedMessage = await protectMessage({
      message,
      passphrase: sessionPassphrase,
      patternBytes: sessionPattern
    });
    writeEditor(editor, protectedMessage.envelope);
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    bypassSend = true;
    const sendButton = composer.querySelector(".mx_MessageComposer_sendMessage");
    if (sendButton) {
      sendButton.click();
    } else {
      editor.dispatchEvent(new KeyboardEvent("keydown", {
        key: "Enter",
        code: "Enter",
        bubbles: true,
        cancelable: true
      }));
    }
    setTimeout(() => {
      bypassSend = false;
    }, 0);
  } finally {
    busy = false;
    composer.classList.remove("zmath-auto-busy");
  }
}

async function protectSelectedFiles(input) {
  if (busy || bypassFile) return;
  const files = Array.from(input.files || []);
  if (!files.length) return;
  if (!isUnlocked()) {
    input.value = "";
    document.getElementById("zmath-auto-panel").hidden = false;
    toast("Unlock ZMath before attaching files.");
    return;
  }
  busy = true;
  try {
    const transfer = new DataTransfer();
    const protectedFiles = await prepareFiles(files);
    for (const file of protectedFiles) transfer.items.add(file);
    input.files = transfer.files;
    bypassFile = true;
    input.dispatchEvent(new Event("change", {bubbles: true}));
    setTimeout(() => {
      bypassFile = false;
    }, 0);
    toast(`${files.length} attachment${files.length === 1 ? "" : "s"} protected before upload.`);
  } finally {
    busy = false;
  }
}

async function prepareFiles(files) {
  const selected = Array.from(files || []);
  if (!selected.length) return [];
  if (isMatrixOnly()) return selected;
  if (!isUnlocked()) {
    const panel = document.getElementById("zmath-auto-panel");
    if (panel) panel.hidden = false;
    toast("Upload blocked: unlock ZMath or explicitly choose Matrix-only sending.");
    throw new Error("ZMath Auto is locked.");
  }
  const output = [];
  for (const file of selected) {
    if (/\.zme1$/i.test(file.name) && file.type === "application/json") {
      output.push(file);
      continue;
    }
    if (file.size > MAX_AUTO_FILE_BYTES) throw new Error("Choose files no larger than 50 MB.");
    const container = await protectPayload({
      bytes: new Uint8Array(await file.arrayBuffer()),
      name: file.name,
      type: file.type || "application/octet-stream",
      kind: "matrix-attachment",
      passphrase: sessionPassphrase,
      patternBytes: sessionPattern,
      context: {
        purpose: "matrix-attachment",
        zmathPolicy: "ZMath-Auto-Policy-2",
        transport: "Matrix-E2EE"
      }
    });
    output.push(new File(
      [JSON.stringify(container)],
      `${file.name}.zme1`,
      {type: "application/json"}
    ));
  }
  toast(`${output.length} attachment${output.length === 1 ? "" : "s"} protected as ZME1 before upload.`);
  return output;
}

async function openIncomingBody(body) {
  if (!isUnlocked() || openedBodies.has(body)) return;
  const envelope = body.innerText.trim();
  if (!envelope.startsWith(MESSAGE_PREFIX)) return;
  try {
    const opened = await openMessage({
      envelope,
      passphrase: sessionPassphrase,
      patternBytes: sessionPattern
    });
    const display = document.createElement("div");
    display.className = "zmath-auto-opened";
    display.textContent = opened.message;
    body.hidden = true;
    body.insertAdjacentElement("afterend", display);
    openedBodies.set(body, display);
  } catch {
    // A room may contain content protected with another pattern. Leave its envelope intact.
  }
}

function queueIncomingScan() {
  if (scanQueued || !isUnlocked()) return;
  scanQueued = true;
  requestAnimationFrame(async () => {
    scanQueued = false;
    const bodies = document.querySelectorAll(".mx_EventTile_body, .mx_MTextBody");
    for (const body of bodies) await openIncomingBody(body);
  });
}

async function openShieldAttachment(anchor) {
  if (!isUnlocked()) {
    document.getElementById("zmath-auto-panel").hidden = false;
    toast("Unlock ZMath to open this attachment.");
    return;
  }
  const href = anchor.href;
  if (!href || (!href.startsWith("blob:") && !href.startsWith("https://") && !href.startsWith("http://"))) {
    throw new Error("Download the .zme1 file and open it in the ZShield workspace.");
  }
  const response = await fetch(href, {credentials: "include"});
  if (!response.ok) throw new Error("The encrypted attachment could not be read.");
  const container = JSON.parse(await response.text());
  const opened = await openContainerPayload({
    container,
    passphrase: sessionPassphrase,
    patternBytes: sessionPattern
  });
  downloadBytes(
    opened.bytes,
    opened.header.payload.name || "opened-file",
    opened.header.payload.type || "application/octet-stream"
  );
  toast("ZMath attachment authenticated and opened locally.");
}

document.addEventListener("keydown", (event) => {
  if (
    bypassSend ||
    isMatrixOnly() ||
    event.key !== "Enter" ||
    event.shiftKey ||
    event.ctrlKey ||
    event.altKey ||
    event.metaKey
  ) return;
  const composer = composerFor(event.target);
  if (!composer || event.target !== editorFor(composer)) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  protectComposerAndSend(composer).catch(showError);
}, true);

document.addEventListener("click", (event) => {
  const target = event.target instanceof Element ? event.target : null;
  if (!target) return;
  const sendButton = target.closest(".mx_MessageComposer_sendMessage");
  if (sendButton && !bypassSend && !isMatrixOnly()) {
    const composer = composerFor(sendButton);
    if (!composer) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    protectComposerAndSend(composer).catch(showError);
    return;
  }
  const attachment = target.closest("a[href]");
  const attachmentName = attachment && (
    attachment.getAttribute("download") ||
    attachment.textContent ||
    attachment.getAttribute("aria-label") ||
    ""
  );
  if (attachment && /\.zme1\s*$/i.test(attachmentName.trim())) {
    event.preventDefault();
    event.stopImmediatePropagation();
    openShieldAttachment(attachment).catch(showError);
  }
}, true);

document.addEventListener("change", (event) => {
  const input = event.target;
  if (
    bypassFile ||
    isMatrixOnly() ||
    !(input instanceof HTMLInputElement) ||
    input.type !== "file" ||
    input.dataset.testid !== "room-upload-context-input" ||
    !(input.files && input.files.length)
  ) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  protectSelectedFiles(input).catch(showError);
}, true);

window.callchatZMathRequired = true;
window.callchatZMathAuto = Object.freeze({
  profile: PROFILE,
  isUnlocked,
  isMatrixOnly,
  prepareFiles
});

new MutationObserver(queueIncomingScan).observe(document.documentElement, {
  childList: true,
  subtree: true
});

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", createUi, {once: true});
} else {
  createUi();
}
