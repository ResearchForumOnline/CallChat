import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

import {openContainerPayload, protectPayload} from "./zshield-core.js";

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

console.log("ZShield ZME1 round-trip, tamper, factor and resource-bound tests: ok");
