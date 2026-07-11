import * as ShieldCore from "./zshield-core.js";
import {parseQuantumFactorFile} from "./qpu-factor-core.js?v=20260711-qfactor1";

(function () {
  "use strict";

  const MAX_BYTES = 50 * 1024 * 1024;
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();
  let shareFile = null;
  let lastMessageEnvelope = "";
  let lastOpenedMessage = "";

  const byId = (id) => document.getElementById(id);

  async function loadQuantumFactor(inputId) {
    const file = byId(inputId).files[0];
    if (!file) return {bytes: new Uint8Array(), evidence: null};
    if (file.size > 32 * 1024) throw new Error("The QPU factor file is too large.");
    const parsed = await parseQuantumFactorFile(decoder.decode(await file.arrayBuffer()));
    return {
      bytes: parsed.factorBytes,
      evidence: {...parsed.evidence, evidenceDigest: parsed.evidenceDigest}
    };
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
      const quantumFactor = await loadQuantumFactor("protect-quantum-factor");
      if (source.payloadType === "matrix-message") {
        const protectedMessage = await ShieldCore.protectMessage({
          message: source.message,
          passphrase: password,
          patternBytes,
          quantumFactorBytes: quantumFactor.bytes,
          qpuBackend: quantumFactor.evidence && quantumFactor.evidence.backend,
          qpuJob: quantumFactor.evidence && quantumFactor.evidence.job_id,
          qpuEvidenceDigest: quantumFactor.evidence && quantumFactor.evidence.evidenceDigest
        });
        lastMessageEnvelope = protectedMessage.envelope;
        byId("message-output").value = lastMessageEnvelope;
        byId("message-fingerprint").textContent = "Envelope fingerprint: " + await ShieldCore.containerFingerprint(protectedMessage.container);
        byId("message-output-wrap").hidden = false;
        byId("copy-message-button").hidden = false;
        byId("message-text").value = "";
        byId("protect-password").value = "";
        byId("protect-confirm").value = "";
        setResult(
          "Message protected locally",
          quantumFactor.evidence
            ? "The independent IonQ QPU factor is required to open this envelope. Share it separately from the ciphertext."
            : "Copy the ZSHIELD1 envelope into a Matrix E2EE room.",
          "success"
        );
        quantumFactor.bytes.fill(0);
        return;
      }
      const container = await ShieldCore.protectPayload({
        bytes: source.bytes,
        name: source.name,
        type: source.type,
        kind: source.payloadType,
        passphrase: password,
        patternBytes,
        quantumFactorBytes: quantumFactor.bytes,
        context: {
          purpose: source.payloadType === "file" ? "matrix-file" : "vault-note",
          zmathPolicy: "ZMath-Shield-Policy-1",
          transport: "Matrix-E2EE",
          qpuBackend: quantumFactor.evidence && quantumFactor.evidence.backend,
          qpuJob: quantumFactor.evidence && quantumFactor.evidence.job_id,
          qpuEvidenceDigest: quantumFactor.evidence && quantumFactor.evidence.evidenceDigest
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
      quantumFactor.bytes.fill(0);
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
      const quantumFactor = await loadQuantumFactor("open-quantum-factor");
      if (byId("open-source-type").value === "message") {
        const openedMessage = await ShieldCore.openMessage({
          envelope: byId("open-message").value,
          passphrase: byId("open-password").value,
          patternBytes,
          quantumFactorBytes: quantumFactor.bytes
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
        quantumFactor.bytes.fill(0);
        return;
      }
      const file = byId("open-file").files[0];
      if (!file) throw new Error("Choose a ZME1 container first.");
      if (file.size > MAX_BYTES * 1.4) throw new Error("This container is too large for the browser workspace.");
      const container = JSON.parse(decoder.decode(await file.arrayBuffer()));
      const opened = await ShieldCore.openContainerPayload({
        container,
        passphrase: byId("open-password").value,
        patternBytes,
        quantumFactorBytes: quantumFactor.bytes
      });
      const output = new Blob([opened.bytes], {type: opened.header.payload.type || "application/octet-stream"});
      const filename = safeName(opened.header.payload.name);
      download(output, filename);
      byId("open-password").value = "";
      setResult("Authenticated and opened", filename + " passed AES-GCM integrity verification.", "success");
      quantumFactor.bytes.fill(0);
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
