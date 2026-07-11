import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

import {
  PROFILE,
  containerFingerprint,
  decodeMessageContainer,
  openContainerPayload,
  openMessage,
  protectMessage,
  protectPayload
} from "./zshield-core.js";

const passphrase = "Correct-Horse-Battery-2026";
const pattern = new TextEncoder().encode("local-pattern-factor");
const plaintext = new TextEncoder().encode("CallChat ZShield round-trip payload");

const container = await protectPayload({
  bytes: plaintext,
  name: "evidence.txt",
  type: "text/plain",
  kind: "file",
  passphrase,
  patternBytes: pattern,
  createdAt: "2026-07-10T00:00:00Z"
});

const opened = await openContainerPayload({container, passphrase, patternBytes: pattern});
assert.deepEqual(opened.bytes, plaintext);
assert.equal(opened.header.payload.name, "evidence.txt");
assert.equal(opened.header.profile, PROFILE);
assert.equal(opened.header.kdf.name, "PBKDF2-SHA-256+HKDF-SHA-256");

await assert.rejects(
  openContainerPayload({
    container,
    passphrase,
    patternBytes: new TextEncoder().encode("wrong-pattern-factor")
  }),
  /Authentication failed/
);

await assert.rejects(
  openContainerPayload({container, passphrase: "Wrong-Passphrase-For-Test", patternBytes: pattern}),
  /Authentication failed/
);

const tampered = structuredClone(container);
tampered.header.payload.name = "changed.txt";
await assert.rejects(
  openContainerPayload({container: tampered, passphrase, patternBytes: pattern}),
  /Authentication failed/
);

await assert.rejects(
  openContainerPayload({container, passphrase, patternBytes: new Uint8Array()}),
  /requires the sender's pattern file/
);

const excessiveWork = structuredClone(container);
excessiveWork.header.kdf.iterations = 999999999;
await assert.rejects(
  openContainerPayload({container: excessiveWork, passphrase, patternBytes: pattern}),
  /KDF profile/
);

const malformedIv = structuredClone(container);
malformedIv.header.cipher.iv = "AAAA";
await assert.rejects(
  openContainerPayload({container: malformedIv, passphrase, patternBytes: pattern}),
  /salt or IV length/
);

const truncatedCiphertext = structuredClone(container);
truncatedCiphertext.ciphertext = truncatedCiphertext.ciphertext.slice(0, -4);
await assert.rejects(
  openContainerPayload({container: truncatedCiphertext, passphrase, patternBytes: pattern}),
  /payload size/
);

const vector = JSON.parse(await readFile(new URL("./test-vectors/zme1-v1.json", import.meta.url), "utf8"));
const vectorOpened = await openContainerPayload({
  container: vector.container,
  passphrase: vector.passphrase,
  patternBytes: Uint8Array.from(Buffer.from(vector.patternBase64, "base64"))
});
assert.equal(Buffer.from(vectorOpened.bytes).toString("base64"), vector.plaintextBase64);

const shieldedMessage = await protectMessage({
  message: "A private Matrix message with a real ZShield layer.",
  passphrase,
  patternBytes: pattern,
  createdAt: "2026-07-10T00:00:00Z"
});
assert.match(shieldedMessage.envelope, /^ZSHIELD1:/);
assert.equal(decodeMessageContainer(shieldedMessage.envelope).header.context.purpose, "matrix-message");
assert.equal(decodeMessageContainer(shieldedMessage.envelope).header.context.zmathPolicy, "ZMath-Shield-Policy-1");
const openedMessage = await openMessage({envelope: shieldedMessage.envelope, passphrase, patternBytes: pattern});
assert.equal(openedMessage.message, "A private Matrix message with a real ZShield layer.");
assert.match(await containerFingerprint(shieldedMessage.container), /^[a-f0-9]{24}$/);

const alteredEnvelope = shieldedMessage.envelope.slice(0, -2) + "AA";
await assert.rejects(
  openMessage({envelope: alteredEnvelope, passphrase, patternBytes: pattern}),
  /malformed|Authentication failed/
);

console.log("ZShield file and message round-trip, tamper, factor and resource-bound tests: ok");
