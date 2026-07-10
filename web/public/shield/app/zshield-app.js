import * as ShieldCore from "./zshield-core.js";

(function () {
  "use strict";

  const FORMAT = "ZME1";
  const VERSION = 1;
  const PROFILE = "ZSHIELD-PBKDF2-AESGCM-1";
  const ITERATIONS = 600000;
  const MAX_BYTES = 50 * 1024 * 1024;
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();
  let shareFile = null;
  let lastMessageEnvelope = "";
  let lastOpenedMessage = "";

  const byId = (id) => document.getElementById(id);

  function randomBytes(length) {
    const value = new Uint8Array(length);
    crypto.getRandomValues(value);
    return value;
  }

  function bytesToBase64(bytes) {
    let value = "";
    const chunk = 0x8000;
    for (let offset = 0; offset < bytes.length; offset += chunk) {
      value += String.fromCharCode.apply(null, bytes.subarray(offset, offset + chunk));
    }
    return btoa(value);
  }

  function base64ToBytes(value) {
    const binary = atob(String(value || ""));
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) {
      bytes[index] = binary.charCodeAt(index);
    }
    return bytes;
  }

  function concatBytes(parts) {
    const total = parts.reduce((sum, part) => sum + part.length, 0);
    const output = new Uint8Array(total);
    let offset = 0;
    for (const part of parts) {
      output.set(part, offset);
      offset += part.length;
    }
    return output;
  }

  function canonical(value) {
    if (Array.isArray(value)) {
      return "[" + value.map(canonical).join(",") + "]";
    }
    if (value && typeof value === "object") {
      return "{" + Object.keys(value).sort().map((key) => JSON.stringify(key) + ":" + canonical(value[key])).join(",") + "}";
    }
    return JSON.stringify(value);
  }

  async function patternDigest(file) {
    if (!file) return new Uint8Array(32);
    return new Uint8Array(await crypto.subtle.digest("SHA-256", await file.arrayBuffer()));
  }

  async function deriveKey(passphrase, patternFile, salt, iterations) {
    if (passphrase.length < 14) {
      throw new Error("Use a passphrase with at least 14 characters.");
    }
    const pattern = await patternDigest(patternFile);
    const material = concatBytes([encoder.encode(passphrase), new Uint8Array([0]), pattern]);
    const imported = await crypto.subtle.importKey("raw", material, "PBKDF2", false, ["deriveKey"]);
    return crypto.subtle.deriveKey(
      {name: "PBKDF2", hash: "SHA-256", salt, iterations},
      imported,
      {name: "AES-GCM", length: 256},
      false,
      ["encrypt", "decrypt"]
    );
  }

  function safeName(value) {
    return String(value || "payload.bin").replace(/[\\/:*?"<>|]+/g, "_").slice(0, 160);
  }

  function download(blob, filename) {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      URL.revokeObjectURL(link.href);
      link.remove();
    }, 1000);
  }

  function setResult(title, detail, kind) {
    const result = byId("shield-result");
    result.className = "shield-result" + (kind ? " " + kind : "");
    result.querySelector("strong").textContent = title;
    result.querySelector("span").textContent = detail;
  }

  function setBusy(button, busy, label) {
    button.disabled = busy;
    button.textContent = busy ? "Working locally..." : label;
  }

  async function ionqResearchReceipt() {
    if (!byId("ionq-receipt").checked) return "";
    const nonce = new Uint8Array(32);
    crypto.getRandomValues(nonce);
    const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", nonce));
    const commitment = Array.from(digest, (byte) => byte.toString(16).padStart(2, "0")).join("");
    const response = await fetch("/api/quantum/ionq/receipt", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({commitment})
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || !result.receipt) {
      throw new Error(result.error && result.error.message || "IonQ research receipt is unavailable.");
    }
    return String(result.receipt);
  }

  async function sourcePayload() {
    if (byId("source-type").value === "message") {
      const text = byId("message-text").value.trim();
      if (!text) throw new Error("Enter a private message first.");
      return {
        name: "zshield-message.txt",
        type: "text/plain;charset=utf-8",
        bytes: encoder.encode(text),
        payloadType: "matrix-message",
        message: text
      };
    }
    if (byId("source-type").value === "note") {
      const text = byId("vault-note").value.trim();
      if (!text) throw new Error("Enter a vault note first.");
      return {
        name: "zshield-vault-note.txt",
        type: "text/plain;charset=utf-8",
        bytes: encoder.encode(text),
        payloadType: "vault-note"
      };
    }
    const file = byId("protect-file").files[0];
    if (!file) throw new Error("Choose a file first.");
    if (file.size > MAX_BYTES) throw new Error("Choose a file no larger than 50 MB.");
    return {
      name: safeName(file.name),
      type: file.type || "application/octet-stream",
      bytes: new Uint8Array(await file.arrayBuffer()),
      payloadType: "file"
    };
  }

  async function protect(event) {
    event.preventDefault();
    const button = byId("protect-button");
    setBusy(button, true, "Protect payload");
    shareFile = null;
    lastMessageEnvelope = "";
    byId("share-button").hidden = true;
    byId("copy-message-button").hidden = true;
    byId("message-output-wrap").hidden = true;
    try {
      const password = byId("protect-password").value;
      if (password !== byId("protect-confirm").value) throw new Error("Passphrases do not match.");
      const source = await sourcePayload();
      const patternFile = byId("protect-pattern").files[0] || null;
      const patternBytes = patternFile ? new Uint8Array(await patternFile.arrayBuffer()) : new Uint8Array();
      const quantumReceipt = await ionqResearchReceipt();
      if (source.payloadType === "matrix-message") {
        const protectedMessage = await ShieldCore.protectMessage({
          message: source.message,
          passphrase: password,
          patternBytes,
          quantumReceipt
        });
        lastMessageEnvelope = protectedMessage.envelope;
        byId("message-output").value = lastMessageEnvelope;
        byId("message-fingerprint").textContent = "Envelope fingerprint: " + await ShieldCore.containerFingerprint(protectedMessage.container);
        byId("message-output-wrap").hidden = false;
        byId("copy-message-button").hidden = false;
        byId("message-text").value = "";
        byId("protect-password").value = "";
        byId("protect-confirm").value = "";
        setResult("Message protected locally", quantumReceipt ? "IonQ simulator receipt authenticated inside the envelope; copy it into a Matrix E2EE room." : "Copy the ZSHIELD1 envelope into a Matrix E2EE room.", "success");
        return;
      }
      const container = await ShieldCore.protectPayload({
        bytes: source.bytes,
        name: source.name,
        type: source.type,
        kind: source.payloadType,
        passphrase: password,
        patternBytes,
        context: {
          purpose: source.payloadType === "file" ? "matrix-file" : "vault-note",
          zmathPolicy: "ZMath-Shield-Policy-1",
          transport: "Matrix-E2EE",
          quantumReceipt
        }
      });
      const blob = new Blob([JSON.stringify(container)], {type: "application/vnd.callchat.zshield+json"});
      const filename = safeName(source.name.replace(/\.[^.]+$/, "")) + ".zme1";
      shareFile = new File([blob], filename, {type: blob.type});
      download(blob, filename);
      if (navigator.canShare && navigator.canShare({files: [shareFile]})) {
        byId("share-button").hidden = false;
      }
      byId("protect-password").value = "";
      byId("protect-confirm").value = "";
      setResult("Protected locally", filename + " is ready to attach in CallChat.", "success");
    } catch (error) {
      setResult("Protection stopped", error.message || "The payload could not be protected.", "error");
    } finally {
      setBusy(button, false, byId("source-type").value === "message" ? "Protect message" : "Protect payload");
    }
  }

  async function openContainer(event) {
    event.preventDefault();
    const button = byId("open-button");
    setBusy(button, true, "Open payload");
    lastOpenedMessage = "";
    byId("copy-opened-button").hidden = true;
    byId("opened-message-wrap").hidden = true;
    try {
      const patternFile = byId("open-pattern").files[0] || null;
      const patternBytes = patternFile ? new Uint8Array(await patternFile.arrayBuffer()) : new Uint8Array();
      if (byId("open-source-type").value === "message") {
        const openedMessage = await ShieldCore.openMessage({
          envelope: byId("open-message").value,
          passphrase: byId("open-password").value,
          patternBytes
        });
        lastOpenedMessage = openedMessage.message;
        byId("opened-message").value = lastOpenedMessage;
        byId("opened-message-context").textContent = "Authenticated context: " +
          (openedMessage.header.context && openedMessage.header.context.zmathPolicy || "ZME1") + " / " +
          (openedMessage.header.context && openedMessage.header.context.transport || "independent");
        byId("opened-message-wrap").hidden = false;
        byId("copy-opened-button").hidden = false;
        byId("open-password").value = "";
        setResult("Message authenticated and opened", "AES-GCM integrity verification passed before plaintext was shown.", "success");
        return;
      }
      const file = byId("open-file").files[0];
      if (!file) throw new Error("Choose a ZME1 container first.");
      if (file.size > MAX_BYTES * 1.4) throw new Error("This container is too large for the browser workspace.");
      const container = JSON.parse(decoder.decode(await file.arrayBuffer()));
      const opened = await ShieldCore.openContainerPayload({
        container,
        passphrase: byId("open-password").value,
        patternBytes
      });
      const output = new Blob([opened.bytes], {type: opened.header.payload.type || "application/octet-stream"});
      const filename = safeName(opened.header.payload.name);
      download(output, filename);
      byId("open-password").value = "";
      setResult("Authenticated and opened", filename + " passed AES-GCM integrity verification.", "success");
    } catch (error) {
      setResult("Open stopped", error.message || "The container could not be opened.", "error");
    } finally {
      setBusy(button, false, byId("open-source-type").value === "message" ? "Open message" : "Open payload");
    }
  }

  function selectTab(mode) {
    const protect = mode === "protect";
    byId("protect-tab").setAttribute("aria-selected", String(protect));
    byId("open-tab").setAttribute("aria-selected", String(!protect));
    byId("protect-panel").hidden = !protect;
    byId("open-panel").hidden = protect;
  }

  function wireDropZone(zoneId, inputId, nameId) {
    const zone = byId(zoneId);
    const input = byId(inputId);
    const update = () => {
      const file = input.files[0];
      if (file) byId(nameId).textContent = file.name + " - " + Math.ceil(file.size / 1024) + " KB";
    };
    input.addEventListener("change", update);
    for (const eventName of ["dragenter", "dragover"]) {
      zone.addEventListener(eventName, (event) => {
        event.preventDefault();
        zone.classList.add("dragging");
      });
    }
    for (const eventName of ["dragleave", "drop"]) {
      zone.addEventListener(eventName, (event) => {
        event.preventDefault();
        zone.classList.remove("dragging");
      });
    }
    zone.addEventListener("drop", (event) => {
      if (!event.dataTransfer.files.length) return;
      const transfer = new DataTransfer();
      transfer.items.add(event.dataTransfer.files[0]);
      input.files = transfer.files;
      update();
    });
  }

  async function copyText(value, successMessage) {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      setResult("Copied", successMessage, "success");
    } catch (error) {
      setResult("Copy stopped", "Select the text and copy it manually; browser clipboard permission was not granted.", "error");
    }
  }

  function updateProtectSource() {
    const source = byId("source-type").value;
    byId("message-field").hidden = source !== "message";
    byId("note-field").hidden = source !== "note";
    byId("protect-file-zone").hidden = source !== "file";
    byId("protect-button").textContent = source === "message" ? "Protect message" : "Protect payload";
  }

  function updateOpenSource() {
    const message = byId("open-source-type").value === "message";
    byId("open-message-wrap").hidden = !message;
    byId("open-file-zone").hidden = message;
    byId("open-button").textContent = message ? "Open message" : "Open payload";
  }

  async function loadSecurityStatus() {
    const box = byId("live-security");
    try {
      const response = await fetch("/api/security-status.json", {cache: "no-store"});
      if (!response.ok) throw new Error("status unavailable");
      const status = await response.json();
      const matrix = status.matrix_e2ee || {};
      if (!matrix.all_current_rooms_encrypted) throw new Error("not all rooms encrypted");
      box.classList.add("verified");
      box.querySelector("strong").textContent = matrix.configured_rooms + "/" + matrix.total_rooms + " current rooms encrypted";
      box.querySelector("small").textContent = status.zero_bot.online ? "Encrypted Zero Bot online" : "Matrix E2EE verified";
    } catch (error) {
      box.querySelector("strong").textContent = "Live status unavailable";
      box.querySelector("small").textContent = "Verify the room padlock before sending";
    }
  }

  byId("protect-tab").addEventListener("click", () => selectTab("protect"));
  byId("open-tab").addEventListener("click", () => selectTab("open"));
  byId("protect-form").addEventListener("submit", protect);
  byId("open-form").addEventListener("submit", openContainer);
  byId("source-type").addEventListener("change", updateProtectSource);
  byId("open-source-type").addEventListener("change", updateOpenSource);
  byId("copy-message-button").addEventListener("click", () => copyText(lastMessageEnvelope, "Paste the complete envelope into CallChat."));
  byId("copy-opened-button").addEventListener("click", () => copyText(lastOpenedMessage, "Authenticated plaintext copied."));
  byId("share-button").addEventListener("click", async () => {
    if (!shareFile) return;
    try {
      await navigator.share({files: [shareFile], title: "ZShield encrypted file"});
    } catch (error) {
      if (error.name !== "AbortError") setResult("Share stopped", "Your device did not accept the encrypted file share.", "error");
    }
  });
  byId("open-form").addEventListener("reset", () => {
    setTimeout(() => {
      lastOpenedMessage = "";
      byId("opened-message").value = "";
      byId("opened-message-wrap").hidden = true;
      byId("copy-opened-button").hidden = true;
      updateOpenSource();
      setResult("Local-only workspace", "Passphrases, pattern files and plaintext are never sent by this page.", "");
    }, 0);
  });

  wireDropZone("protect-file-zone", "protect-file", "protect-file-name");
  wireDropZone("open-file-zone", "open-file", "open-file-name");
  updateProtectSource();
  updateOpenSource();
  loadSecurityStatus();
}());
