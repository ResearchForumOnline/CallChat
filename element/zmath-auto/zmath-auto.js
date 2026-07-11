import {
  MESSAGE_PREFIX,
  PROFILE,
  containerFingerprint,
  openContainerPayload,
  openMessage,
  protectMessage,
  protectPayload
} from "/shield/app/zshield-core.js";
import {parseQuantumFactorFile} from "/shield/app/qpu-factor-core.js?v=20260711-qfactor1";

const VAULT_KEY = "callchat.zmath.auto.v1";
const MODE_KEY = "callchat.zmath.mode.v1";
const TRUSTED_PROFILE_KEY = "callchat.zmath.trusted-profile.v1";
const DEVICE_DB_NAME = "callchat-zmath-device-v1";
const DEVICE_DB_STORE = "keys";
const DEVICE_KEY_ID = "trusted-profile-key";
const DEVICE_PROFILE_DOMAIN = "CallChat-ZMath-Trusted-Device-1";
const VAULT_ITERATIONS = 600000;
const MAX_AUTO_FILE_BYTES = 50 * 1024 * 1024;
const MEDIA_ROOT_DOMAIN = "CallChat-ZMath-Media-Root-v1";
const MEDIA_ROOM_DOMAIN = "CallChat-ZMath-Media-Room-v1";
const encoder = new TextEncoder();
const MODULE_OWNER = !window.__callchatZMathAutoModuleV2;
if (MODULE_OWNER) window.__callchatZMathAutoModuleV2 = true;

let sessionPassphrase = "";
let sessionPattern = null;
let sessionPatternName = "";
let sessionMediaRoot = null;
let sessionQuantumFactor = null;
let sessionQuantumEvidence = null;
let sessionQuantumFactorFile = null;
let pendingPattern = null;
let pendingPatternName = "";
let pendingQuantumFactorFile = null;
let bypassSend = false;
let bypassFile = false;
let busy = false;
let scanQueued = false;
let scanAgain = false;
let setupBusy = false;
let automaticRestore = null;
let trustedProfileAvailable = false;
let profileEpoch = 0;
let recoveryTimer = null;
const openedBodies = new Map();
const openingBodies = new WeakSet();
const preparedCallSecrets = new Map();

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

function openDeviceDatabase() {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) {
      reject(new Error("Trusted-device storage is unavailable in this browser."));
      return;
    }
    const request = indexedDB.open(DEVICE_DB_NAME, 1);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(DEVICE_DB_STORE)) {
        request.result.createObjectStore(DEVICE_DB_STORE);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("Trusted-device storage could not be opened."));
  });
}

async function deviceKey(create = false) {
  const database = await openDeviceDatabase();
  try {
    const existing = await new Promise((resolve, reject) => {
      const transaction = database.transaction(DEVICE_DB_STORE, "readonly");
      const request = transaction.objectStore(DEVICE_DB_STORE).get(DEVICE_KEY_ID);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error || new Error("Trusted-device key could not be read."));
    });
    if (existing || !create) return existing;
    const generated = await crypto.subtle.generateKey(
      {name: "AES-GCM", length: 256},
      false,
      ["encrypt", "decrypt"]
    );
    await new Promise((resolve, reject) => {
      const transaction = database.transaction(DEVICE_DB_STORE, "readwrite");
      transaction.objectStore(DEVICE_DB_STORE).put(generated, DEVICE_KEY_ID);
      transaction.oncomplete = resolve;
      transaction.onerror = () => reject(transaction.error || new Error("Trusted-device key could not be saved."));
      transaction.onabort = () => reject(transaction.error || new Error("Trusted-device key storage was cancelled."));
    });
    return generated;
  } finally {
    database.close();
  }
}

async function deleteDeviceProfile() {
  const database = await openDeviceDatabase();
  try {
    await new Promise((resolve, reject) => {
      const transaction = database.transaction(DEVICE_DB_STORE, "readwrite");
      transaction.objectStore(DEVICE_DB_STORE).delete(DEVICE_KEY_ID);
      transaction.objectStore(DEVICE_DB_STORE).delete(TRUSTED_PROFILE_KEY);
      transaction.oncomplete = resolve;
      transaction.onerror = () => reject(transaction.error || new Error("Trusted-device key could not be removed."));
      transaction.onabort = () => reject(transaction.error || new Error("Trusted-device key removal was cancelled."));
    });
  } finally {
    database.close();
  }
}

function hasTrustedDeviceProfile() {
  return trustedProfileAvailable;
}

async function saveTrustedDeviceProfile(passphrase, patternBytes, name, quantumFactorFile) {
  const key = await deviceKey(true);
  const iv = randomBytes(12);
  const plaintext = encoder.encode(JSON.stringify({
    version: 2,
    passphrase,
    pattern: bytesToBase64(patternBytes),
    name: String(name || "callchat-pattern.png").slice(0, 128),
    quantumFactorFile: quantumFactorFile || null
  }));
  try {
    const ciphertext = new Uint8Array(await crypto.subtle.encrypt(
      {name: "AES-GCM", iv, additionalData: encoder.encode(DEVICE_PROFILE_DOMAIN)},
      key,
      plaintext
    ));
    const record = {
      version: 1,
      iv: bytesToBase64(iv),
      ciphertext: bytesToBase64(ciphertext)
    };
    const database = await openDeviceDatabase();
    try {
      await new Promise((resolve, reject) => {
        const transaction = database.transaction(DEVICE_DB_STORE, "readwrite");
        transaction.objectStore(DEVICE_DB_STORE).put(record, TRUSTED_PROFILE_KEY);
        transaction.oncomplete = resolve;
        transaction.onerror = () => reject(transaction.error || new Error("Trusted-device profile could not be saved."));
        transaction.onabort = () => reject(transaction.error || new Error("Trusted-device profile storage was cancelled."));
      });
      trustedProfileAvailable = true;
    } finally {
      database.close();
    }
  } finally {
    plaintext.fill(0);
  }
}

async function loadTrustedDeviceProfile() {
  const database = await openDeviceDatabase();
  let record;
  try {
    record = await new Promise((resolve, reject) => {
      const transaction = database.transaction(DEVICE_DB_STORE, "readonly");
      const request = transaction.objectStore(DEVICE_DB_STORE).get(TRUSTED_PROFILE_KEY);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error || new Error("Trusted-device profile could not be read."));
    });
  } finally {
    database.close();
  }
  trustedProfileAvailable = Boolean(record);
  if (!record) return null;
  if (record.version !== 1 || base64ToBytes(record.iv).length !== 12) {
    throw new Error("The previous automatic profile is unavailable. Reset this device or import recovery factors.");
  }
  const key = await deviceKey(false);
  if (!key) throw new Error("The previous automatic profile is unavailable. Reset this device or import recovery factors.");
  let plaintext;
  try {
    plaintext = new Uint8Array(await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: base64ToBytes(record.iv),
        additionalData: encoder.encode(DEVICE_PROFILE_DOMAIN)
      },
      key,
      base64ToBytes(record.ciphertext)
    ));
  } catch {
    throw new Error("The previous automatic profile is unavailable. Reset this device or import recovery factors.");
  }
  try {
    const profile = JSON.parse(new TextDecoder().decode(plaintext));
    const pattern = base64ToBytes(profile.pattern);
    if (![1, 2].includes(profile.version) || String(profile.passphrase || "").length < 14 || !pattern.length) {
      throw new Error("The trusted-device profile is incomplete.");
    }
    return {
      passphrase: String(profile.passphrase),
      pattern,
      name: String(profile.name || "callchat-pattern.png"),
      quantumFactorFile: profile.version === 2 ? profile.quantumFactorFile || null : null
    };
  } finally {
    plaintext.fill(0);
  }
}

async function clearTrustedDeviceProfile() {
  try {
    await deleteDeviceProfile();
  } catch {
    // The encrypted profile is already removed; a missing device key is harmless.
  }
  trustedProfileAvailable = false;
}

function bytesToBase64Url(bytes) {
  return bytesToBase64(bytes).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function joinBytes(...parts) {
  const length = parts.reduce((total, part) => total + part.length, 0);
  const output = new Uint8Array(length);
  let offset = 0;
  for (const part of parts) {
    output.set(part, offset);
    offset += part.length;
  }
  return output;
}

function randomBytes(length) {
  const output = new Uint8Array(length);
  crypto.getRandomValues(output);
  return output;
}

function isUnlocked() {
  return Boolean(
    sessionPassphrase &&
    sessionPattern &&
    sessionPattern.length &&
    sessionMediaRoot &&
    sessionMediaRoot.length === 32
  );
}

function isMatrixOnly() {
  return localStorage.getItem(MODE_KEY) === "matrix";
}

function setMatrixOnly(enabled) {
  localStorage.setItem(MODE_KEY, enabled ? "matrix" : "shield");
  if (enabled) {
    for (const secret of preparedCallSecrets.values()) secret.fill(0);
    preparedCallSecrets.clear();
  }
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

async function deriveMediaRoot(passphrase, patternBytes, quantumFactorBytes = null) {
  const domain = encoder.encode(MEDIA_ROOT_DOMAIN);
  const patternHash = new Uint8Array(await crypto.subtle.digest("SHA-256", patternBytes));
  const saltInput = joinBytes(domain, new Uint8Array([0]), patternHash);
  const salt = new Uint8Array(await crypto.subtle.digest("SHA-256", saltInput));
  const passphraseKey = await crypto.subtle.importKey(
    "raw",
    encoder.encode(passphrase),
    "PBKDF2",
    false,
    ["deriveBits"]
  );
  const passphraseFactor = new Uint8Array(await crypto.subtle.deriveBits(
    {name: "PBKDF2", hash: "SHA-256", salt, iterations: VAULT_ITERATIONS},
    passphraseKey,
    256
  ));
  const quantumFactorHash = quantumFactorBytes && quantumFactorBytes.length
    ? new Uint8Array(await crypto.subtle.digest("SHA-256", quantumFactorBytes))
    : new Uint8Array();
  const ikmBytes = quantumFactorHash.length
    ? joinBytes(passphraseFactor, new Uint8Array([0]), patternHash, new Uint8Array([0]), quantumFactorHash)
    : joinBytes(passphraseFactor, new Uint8Array([0]), patternHash);
  const ikm = await crypto.subtle.importKey("raw", ikmBytes, "HKDF", false, ["deriveBits"]);
  const root = new Uint8Array(await crypto.subtle.deriveBits(
    {name: "HKDF", hash: "SHA-256", salt, info: domain},
    ikm,
    256
  ));
  patternHash.fill(0);
  saltInput.fill(0);
  salt.fill(0);
  passphraseFactor.fill(0);
  quantumFactorHash.fill(0);
  ikmBytes.fill(0);
  return root;
}

function quantumContext() {
  if (!sessionQuantumEvidence || !sessionQuantumFactor) return {};
  return {
    quantumFactorBytes: sessionQuantumFactor,
    qpuBackend: sessionQuantumEvidence.backend,
    qpuJob: sessionQuantumEvidence.job_id,
    qpuEvidenceDigest: sessionQuantumEvidence.evidenceDigest
  };
}

function assertCallProtectionReady() {
  if (isMatrixOnly()) {
    const panel = document.getElementById("zmath-auto-panel");
    if (panel) panel.hidden = false;
    toast("Call blocked: turn off Matrix-only mode and unlock ZMath for protected calls.");
    throw new Error("ZMath media protection is disabled in Matrix-only mode.");
  }
  if (!isUnlocked()) {
    const panel = document.getElementById("zmath-auto-panel");
    if (panel) panel.hidden = false;
    toast("Call blocked: unlock ZMath with the shared passphrase and exact pattern image.");
    throw new Error("ZMath must be unlocked before joining a voice or video call.");
  }
}

async function prepareCallSecret(roomId) {
  if (!isUnlocked() && !isMatrixOnly()) await restoreAutomaticSetup();
  assertCallProtectionReady();
  if (typeof roomId !== "string" || !roomId) throw new Error("The call room ID is unavailable.");
  const domain = encoder.encode(MEDIA_ROOM_DOMAIN);
  const room = encoder.encode(roomId);
  const saltInput = joinBytes(domain, new Uint8Array([0]), room);
  const salt = new Uint8Array(await crypto.subtle.digest("SHA-256", saltInput));
  const root = await crypto.subtle.importKey("raw", sessionMediaRoot, "HKDF", false, ["deriveBits"]);
  const roomKey = new Uint8Array(await crypto.subtle.deriveBits(
    {name: "HKDF", hash: "SHA-256", salt, info: domain},
    root,
    256
  ));
  const previous = preparedCallSecrets.get(roomId);
  if (previous) previous.fill(0);
  preparedCallSecrets.set(roomId, roomKey);
  saltInput.fill(0);
  salt.fill(0);
}

function requireCallSecret(roomId) {
  assertCallProtectionReady();
  const roomKey = preparedCallSecrets.get(roomId);
  if (!roomKey) throw new Error("The ZMath room media key was not prepared. Call blocked.");
  return `ZMATHCALL1.${bytesToBase64Url(roomKey)}`;
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

async function generatePatternImage({download = true} = {}) {
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
  if (download) downloadBytes(pendingPattern, pendingPatternName, "image/png");
  updatePatternMeta();
  if (download) toast("Recovery pattern downloaded. Keep it separately from the passphrase.");
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

async function activateProfile(passphrase, pattern, name, {trusted = false, quantumFactorFile = null} = {}) {
  if (String(passphrase || "").length < 14) throw new Error("Use a passphrase with at least 14 characters.");
  if (!(pattern instanceof Uint8Array) || !pattern.length) throw new Error("The exact pattern image is required.");
  const parsedFactor = quantumFactorFile
    ? await parseQuantumFactorFile(quantumFactorFile, {requireHardware: true})
    : null;
  const mediaRoot = await deriveMediaRoot(passphrase, pattern, parsedFactor && parsedFactor.factorBytes);
  if (sessionPattern) sessionPattern.fill(0);
  if (sessionMediaRoot) sessionMediaRoot.fill(0);
  if (sessionQuantumFactor) sessionQuantumFactor.fill(0);
  for (const secret of preparedCallSecrets.values()) secret.fill(0);
  preparedCallSecrets.clear();
  sessionPassphrase = passphrase;
  sessionPattern = pattern.slice();
  sessionPatternName = String(name || "callchat-pattern.png");
  sessionMediaRoot = mediaRoot;
  sessionQuantumFactor = parsedFactor ? parsedFactor.factorBytes : null;
  sessionQuantumEvidence = parsedFactor ? {
    ...parsedFactor.evidence,
    evidenceDigest: parsedFactor.evidenceDigest
  } : null;
  sessionQuantumFactorFile = quantumFactorFile || null;
  profileEpoch += 1;
  pendingPattern = null;
  pendingPatternName = "";
  pendingQuantumFactorFile = null;
  if (trusted) {
    await saveTrustedDeviceProfile(
      passphrase,
      sessionPattern,
      sessionPatternName,
      sessionQuantumFactorFile
    );
  }
  const input = document.getElementById("zmath-auto-passphrase");
  if (input) input.value = "";
  setMatrixOnly(false);
  updateUi();
  queueIncomingScan();
}

async function createAutomaticSetup() {
  if (setupBusy) return;
  setupBusy = true;
  updateUi();
  try {
    const passphrase = generatePassphrase();
    const generated = await generatePatternImage({download: true});
    await activateProfile(passphrase, generated.bytes, generated.name, {trusted: true});
    const recovery = document.getElementById("zmath-auto-recovery");
    const recoveryCode = document.getElementById("zmath-auto-recovery-code");
    recovery.hidden = false;
    recoveryCode.textContent = passphrase;
    clearTimeout(recoveryTimer);
    recoveryTimer = setTimeout(hideRecoveryCode, 90000);
    toast("Automatic protection is active. Save the recovery passphrase separately from the downloaded pattern.");
  } finally {
    setupBusy = false;
    updateUi();
  }
}

async function restoreAutomaticSetup({notify = false} = {}) {
  if (isUnlocked()) return true;
  if (isMatrixOnly()) return false;
  if (!automaticRestore) {
    automaticRestore = (async () => {
      const profile = await loadTrustedDeviceProfile();
      if (!profile) {
        updateUi();
        return false;
      }
      await activateProfile(profile.passphrase, profile.pattern, profile.name, {
        quantumFactorFile: profile.quantumFactorFile
      });
      profile.pattern.fill(0);
      return true;
    })();
  }
  try {
    const restored = await automaticRestore;
    if (restored && notify) toast("Automatic protection restored for this trusted device.");
    return restored;
  } finally {
    automaticRestore = null;
  }
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
      <div class="zmath-auto-simple">
        <button class="zmath-auto-primary zmath-auto-setup" id="zmath-auto-setup" type="button">Turn on automatic protection</button>
        <p id="zmath-auto-device-state">One action creates a protected profile and restores it automatically in this trusted browser.</p>
      </div>
      <div class="zmath-auto-recovery" id="zmath-auto-recovery" hidden>
          <strong>Save this passphrase now</strong>
          <code id="zmath-auto-recovery-code"></code>
          <button id="zmath-auto-copy-recovery" type="button">Copy passphrase</button>
          <button id="zmath-auto-hide-recovery" type="button">Hide recovery code</button>
          <small>It is shown once here. Keep it separately from the downloaded pattern image for recovery and approved device sharing.</small>
      </div>
      <details class="zmath-auto-advanced" id="zmath-auto-advanced">
        <summary>Advanced options</summary>
        <div class="zmath-auto-advanced-body">
          <p class="zmath-auto-meta">Import the same shared passphrase and exact pattern on approved devices that must open protected room content.</p>
          <label class="zmath-auto-field">
            <span>Shared passphrase</span>
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
          <label class="zmath-auto-field">
            <span>IonQ hardware factor (optional)</span>
            <input id="zmath-auto-quantum-factor" type="file" accept="application/json,.zqf">
          </label>
          <p class="zmath-auto-meta" id="zmath-auto-quantum-meta">No QPU factor loaded. Standard ZMath protection remains active.</p>
          <div class="zmath-auto-actions">
            <button id="zmath-auto-clear-quantum" type="button">Remove QPU factor</button>
          </div>
          <div class="zmath-auto-row">
            <label><input id="zmath-auto-trusted" type="checkbox" checked> Auto-unlock on this trusted device</label>
          </div>
          <div class="zmath-auto-row">
            <label><input id="zmath-auto-matrix-only" type="checkbox"> Matrix-only sending</label>
          </div>
          <div class="zmath-auto-actions">
            <button class="zmath-auto-primary" id="zmath-auto-unlock" type="button">Use shared profile</button>
            <button id="zmath-auto-lock" type="button">Pause this session</button>
            <button class="zmath-auto-danger" id="zmath-auto-forget" type="button">Reset this device</button>
          </div>
          <div class="zmath-auto-diagnostic">
            <button id="zmath-auto-self-test" type="button">Run encryption self-test</button>
            <p id="zmath-auto-self-test-result">Not run in this session.</p>
          </div>
          <p class="zmath-auto-meta">Content profile: <span id="zmath-auto-profile"></span></p>
          <p class="zmath-auto-meta">Call profile: <span id="zmath-auto-call-profile">ZMATH-MATRIXRTC-LIVEKIT-1</span></p>
        </div>
      </details>
    </div>`;
  const toastElement = document.createElement("div");
  toastElement.id = "zmath-auto-toast";
  toastElement.hidden = true;
  toastElement.setAttribute("role", "status");
  document.body.append(launcher, panel, toastElement);

  launcher.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
  });
  panel.querySelector(".zmath-auto-close").addEventListener("click", () => {
    panel.hidden = true;
  });
  document.getElementById("zmath-auto-setup").addEventListener("click", () => {
    const action = hasTrustedDeviceProfile()
      ? restoreAutomaticSetup({notify: true})
      : createAutomaticSetup();
    action.catch(showError);
  });
  document.getElementById("zmath-auto-copy-recovery").addEventListener("click", async () => {
    const value = document.getElementById("zmath-auto-recovery-code").textContent || "";
    if (!value) return;
    await navigator.clipboard.writeText(value);
    hideRecoveryCode();
    toast("Passphrase copied. Store it separately from the pattern image.");
  });
  document.getElementById("zmath-auto-hide-recovery").addEventListener("click", hideRecoveryCode);
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
  document.getElementById("zmath-auto-quantum-factor").addEventListener("change", (event) => {
    (async () => {
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      if (file.size > 32768) throw new Error("The QPU factor file is unexpectedly large.");
      const value = await file.text();
      const parsed = await parseQuantumFactorFile(value, {requireHardware: true});
      parsed.factorBytes.fill(0);
      pendingQuantumFactorFile = value;
      updateQuantumMeta(parsed.evidence, file.name);
    })().catch(showError);
  });
  document.getElementById("zmath-auto-clear-quantum").addEventListener("click", () => {
    pendingQuantumFactorFile = null;
    const input = document.getElementById("zmath-auto-quantum-factor");
    if (input) input.value = "";
    updateQuantumMeta();
    toast("The pending QPU factor was removed. Apply the shared profile to change the active session.");
  });
  document.getElementById("zmath-auto-unlock").addEventListener("click", () => {
    unlock().catch(showError);
  });
  document.getElementById("zmath-auto-lock").addEventListener("click", lock);
  document.getElementById("zmath-auto-forget").addEventListener("click", async () => {
    localStorage.removeItem(VAULT_KEY);
    await clearTrustedDeviceProfile();
    pendingPattern = null;
    pendingPatternName = "";
    pendingQuantumFactorFile = null;
    lock();
    updatePatternMeta();
    toast("ZMath was reset on this device. Matrix E2EE remains available.");
  });
  document.getElementById("zmath-auto-self-test").addEventListener("click", () => {
    runSelfTest().catch(showError);
  });
  document.getElementById("zmath-auto-matrix-only").addEventListener("change", (event) => {
    setMatrixOnly(event.target.checked);
  });
  document.getElementById("zmath-auto-profile").textContent = PROFILE;
  updateUi();
  restoreAutomaticSetup({notify: true}).catch((error) => {
    const advanced = document.getElementById("zmath-auto-advanced");
    if (advanced) advanced.open = true;
    showError(error);
  });
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

function updateQuantumMeta(evidence = sessionQuantumEvidence, name = "") {
  const element = document.getElementById("zmath-auto-quantum-meta");
  if (!element) return;
  if (!evidence) {
    element.textContent = "No QPU factor loaded. Standard ZMath protection remains active.";
    return;
  }
  const job = String(evidence.job_id || "").slice(0, 8);
  element.textContent = `${name ? `${name} · ` : ""}IonQ ${evidence.backend} hardware factor · job ${job}`;
}

function hideRecoveryCode() {
  clearTimeout(recoveryTimer);
  recoveryTimer = null;
  const recovery = document.getElementById("zmath-auto-recovery");
  const code = document.getElementById("zmath-auto-recovery-code");
  if (code) code.textContent = "";
  if (recovery) recovery.hidden = true;
}

function updateUi() {
  const launcher = document.getElementById("zmath-auto-launcher");
  const state = document.getElementById("zmath-auto-state");
  const setup = document.getElementById("zmath-auto-setup");
  const deviceState = document.getElementById("zmath-auto-device-state");
  const matrixOnly = isMatrixOnly();
  if (!launcher || !state) return;
  document.getElementById("zmath-auto-matrix-only").checked = matrixOnly;
  const callProfile = document.getElementById("zmath-auto-call-profile");
  if (callProfile) {
    callProfile.textContent = sessionQuantumFactor
      ? "ZMATH-MATRIXRTC-LIVEKIT-QPUFACTOR-1"
      : "ZMATH-MATRIXRTC-LIVEKIT-1";
  }
  if (setup) {
    setup.disabled = setupBusy;
    setup.hidden = matrixOnly || (isUnlocked() && !setupBusy);
    setup.textContent = setupBusy
      ? "Creating protected profile..."
      : hasTrustedDeviceProfile()
        ? "Restore automatic protection"
        : "Turn on automatic protection";
  }
  if (matrixOnly) {
    launcher.textContent = "Matrix only";
    launcher.dataset.state = "matrix";
    state.textContent = "ZMath protection is paused. Matrix end-to-end encryption continues normally.";
    state.dataset.state = "matrix";
    if (deviceState) deviceState.textContent = "Turn off Matrix-only mode in Advanced options to restore automatic protection.";
  } else if (isUnlocked()) {
    launcher.textContent = "ZMath protected";
    launcher.dataset.state = "ready";
    state.textContent = sessionQuantumFactor
      ? "ZMath protection with an IonQ hardware-linked factor is active for messages, selected attachments, voice and video in this browser session."
      : "Automatic protection is active for messages, selected attachments, voice and video in this browser session.";
    state.dataset.state = "ready";
    if (deviceState) {
      deviceState.textContent = hasTrustedDeviceProfile()
        ? "This trusted browser will restore the encrypted profile automatically."
        : "This shared profile is active for the current browser session.";
    }
  } else {
    launcher.textContent = "ZMath locked";
    launcher.dataset.state = "locked";
    state.textContent = "Protection is paused. Turn it on automatically, or import a shared profile under Advanced options.";
    state.dataset.state = "locked";
    if (deviceState) {
      deviceState.textContent = hasTrustedDeviceProfile()
        ? "A trusted-device profile is ready to restore automatically."
        : "One action creates a protected profile and restores it automatically in this trusted browser.";
    }
  }
  updatePatternMeta();
  updateQuantumMeta();
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
  const trusted = document.getElementById("zmath-auto-trusted").checked;
  await activateProfile(passphrase, pattern, name, {
    trusted,
    quantumFactorFile: pendingQuantumFactorFile,
  });
  if (!trusted) await clearTrustedDeviceProfile();
  updateUi();
  toast(trusted
    ? "Shared profile active and automatic unlock enabled for this trusted device."
    : "Shared profile active for this browser session.");
}

function lock() {
  profileEpoch += 1;
  hideRecoveryCode();
  sessionPassphrase = "";
  if (sessionPattern) sessionPattern.fill(0);
  if (sessionMediaRoot) sessionMediaRoot.fill(0);
  if (sessionQuantumFactor) sessionQuantumFactor.fill(0);
  sessionPattern = null;
  sessionPatternName = "";
  sessionMediaRoot = null;
  sessionQuantumFactor = null;
  sessionQuantumEvidence = null;
  sessionQuantumFactorFile = null;
  for (const secret of preparedCallSecrets.values()) secret.fill(0);
  preparedCallSecrets.clear();
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
    ...quantumContext(),
    context: {
      purpose: "local-self-test",
      zmathPolicy: "ZMath-Auto-Policy-2",
      transport: "local-only"
    }
  });
  const opened = await openContainerPayload({
    container,
    passphrase: sessionPassphrase,
    patternBytes: sessionPattern,
    quantumFactorBytes: sessionQuantumFactor
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
  if (!isUnlocked() && !isMatrixOnly()) await restoreAutomaticSetup();
  if (!isUnlocked()) {
    document.getElementById("zmath-auto-panel").hidden = false;
    toast("Turn on automatic protection, or use Advanced options to import a shared profile.");
    return;
  }
  busy = true;
  composer.classList.add("zmath-auto-busy");
  try {
    const protectedMessage = await protectMessage({
      message,
      passphrase: sessionPassphrase,
      patternBytes: sessionPattern,
      ...quantumContext()
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
  if (!isUnlocked() && !isMatrixOnly()) await restoreAutomaticSetup();
  if (!isUnlocked()) {
    input.value = "";
    document.getElementById("zmath-auto-panel").hidden = false;
    toast("Turn on automatic protection before attaching files.");
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
  if (!isUnlocked()) await restoreAutomaticSetup();
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
      ...quantumContext(),
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

function openedDisplayFor(body) {
  let display = openedBodies.get(body);
  if (display && display.isConnected) return display;
  openedBodies.delete(body);
  const adjacent = [];
  let sibling = body.nextElementSibling;
  while (sibling && sibling.classList.contains("zmath-auto-opened")) {
    adjacent.push(sibling);
    sibling = sibling.nextElementSibling;
  }
  display = adjacent.shift() || document.createElement("div");
  for (const duplicate of adjacent) duplicate.remove();
  display.className = "zmath-auto-opened";
  if (!display.isConnected) body.insertAdjacentElement("afterend", display);
  openedBodies.set(body, display);
  return display;
}

function stageIncomingBody(body) {
  if (!isUnlocked() || openingBodies.has(body)) return null;
  const existing = openedBodies.get(body);
  if (existing && existing.isConnected) {
    if (existing.dataset.state === "opened" || existing.dataset.state === "opening") return null;
    if (existing.dataset.state === "locked" && Number(existing.dataset.profileEpoch) === profileEpoch) return null;
  }
  const envelope = String(body.textContent || "").trim();
  if (!envelope.startsWith(MESSAGE_PREFIX)) return null;
  openingBodies.add(body);
  const display = openedDisplayFor(body);
  display.dataset.state = "opening";
  display.dataset.profileEpoch = String(profileEpoch);
  display.textContent = "Opening protected message...";
  body.hidden = true;
  return {body, display, envelope, epoch: profileEpoch};
}

async function openStagedBody(staged) {
  const {body, display, envelope, epoch} = staged;
  try {
    const opened = await openMessage({
      envelope,
      passphrase: sessionPassphrase,
      patternBytes: sessionPattern,
      quantumFactorBytes: sessionQuantumFactor
    });
    if (epoch !== profileEpoch || !isUnlocked() || !body.isConnected) {
      display.remove();
      openedBodies.delete(body);
      if (body.isConnected) body.hidden = false;
      return;
    }
    display.textContent = opened.message;
    display.dataset.state = "opened";
  } catch {
    if (epoch === profileEpoch && body.isConnected) {
      display.textContent = "Protected ZMath message. Unlock the matching shared profile to open it.";
      display.dataset.state = "locked";
      display.dataset.profileEpoch = String(profileEpoch);
    }
  } finally {
    openingBodies.delete(body);
  }
}

function incomingBodyCandidates() {
  const seenEvents = new Set();
  const candidates = Array.from(document.querySelectorAll(".mx_EventTile_body, .mx_MTextBody")).reverse();
  return candidates.filter((body) => {
    if (body.classList.contains("mx_EventTile_body") && body.querySelector(".mx_MTextBody")) return false;
    if (!String(body.textContent || "").trim().startsWith(MESSAGE_PREFIX)) return false;
    const event = body.closest(".mx_EventTile") || body;
    if (seenEvents.has(event)) return false;
    seenEvents.add(event);
    return true;
  });
}

async function runIncomingScan() {
  do {
    scanAgain = false;
    const staged = incomingBodyCandidates()
      .map(stageIncomingBody)
      .filter(Boolean);
    for (let offset = 0; offset < staged.length; offset += 2) {
      await Promise.all(staged.slice(offset, offset + 2).map(openStagedBody));
    }
  } while (scanAgain && isUnlocked());
}

function queueIncomingScan() {
  if (!isUnlocked()) return;
  if (scanQueued) {
    scanAgain = true;
    return;
  }
  scanQueued = true;
  requestAnimationFrame(() => {
    runIncomingScan().catch(showError).finally(() => {
      scanQueued = false;
      if (scanAgain && isUnlocked()) queueIncomingScan();
    });
  });
}

async function openShieldAttachment(anchor) {
  if (!isUnlocked() && !isMatrixOnly()) await restoreAutomaticSetup();
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
    patternBytes: sessionPattern,
    quantumFactorBytes: sessionQuantumFactor
  });
  downloadBytes(
    opened.bytes,
    opened.header.payload.name || "opened-file",
    opened.header.payload.type || "application/octet-stream"
  );
  toast("ZMath attachment authenticated and opened locally.");
}

if (MODULE_OWNER) {
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
window.callchatZMathCallRequired = true;
window.callchatZMathAuto = Object.freeze({
  version: "2026.07.11-renderer2",
  profile: PROFILE,
  isUnlocked,
  isMatrixOnly,
  prepareFiles,
  prepareCallSecret,
  requireCallSecret
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
}
