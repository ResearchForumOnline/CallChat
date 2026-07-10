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

  async function sourcePayload() {
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
    byId("share-button").hidden = true;
    try {
      const password = byId("protect-password").value;
      if (password !== byId("protect-confirm").value) throw new Error("Passphrases do not match.");
      const source = await sourcePayload();
      const patternFile = byId("protect-pattern").files[0] || null;
      const patternBytes = patternFile ? new Uint8Array(await patternFile.arrayBuffer()) : new Uint8Array();
      const container = await ShieldCore.protectPayload({
        bytes: source.bytes,
        name: source.name,
        type: source.type,
        kind: source.payloadType,
        passphrase: password,
        patternBytes
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
      setBusy(button, false, "Protect payload");
    }
  }

  async function openContainer(event) {
    event.preventDefault();
    const button = byId("open-button");
    setBusy(button, true, "Open payload");
    try {
      const file = byId("open-file").files[0];
      if (!file) throw new Error("Choose a ZME1 container first.");
      if (file.size > MAX_BYTES * 1.4) throw new Error("This container is too large for the browser workspace.");
      const container = JSON.parse(decoder.decode(await file.arrayBuffer()));
      const patternFile = byId("open-pattern").files[0] || null;
      const patternBytes = patternFile ? new Uint8Array(await patternFile.arrayBuffer()) : new Uint8Array();
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
      setBusy(button, false, "Open payload");
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
  byId("source-type").addEventListener("change", () => {
    const note = byId("source-type").value === "note";
    byId("note-field").hidden = !note;
    byId("protect-file-zone").hidden = note;
  });
  byId("share-button").addEventListener("click", async () => {
    if (!shareFile) return;
    try {
      await navigator.share({files: [shareFile], title: "ZShield encrypted file"});
    } catch (error) {
      if (error.name !== "AbortError") setResult("Share stopped", "Your device did not accept the encrypted file share.", "error");
    }
  });
  byId("open-form").addEventListener("reset", () => setResult("Local-only workspace", "Passphrases, pattern files and plaintext are never sent by this page.", ""));

  wireDropZone("protect-file-zone", "protect-file", "protect-file-name");
  wireDropZone("open-file-zone", "open-file", "open-file-name");
  loadSecurityStatus();
}());
