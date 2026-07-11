import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const source = await readFile(new URL("./zmath-auto.js", import.meta.url), "utf8");

assert.match(source, /\.mx_MessageComposer_sendMessage/);
assert.match(source, /addEventListener\("keydown"[\s\S]*true\)/);
assert.match(source, /addEventListener\("change"[\s\S]*true\)/);
assert.match(source, /room-upload-context-input/);
assert.match(source, /protectMessage/);
assert.match(source, /protectPayload/);
assert.match(source, /openMessage/);
assert.match(source, /openContainerPayload/);
assert.match(source, /MutationObserver/);
assert.match(source, /Matrix-only sending/);
assert.doesNotMatch(source, /openai|anthropic|gemini|ai api/i);

console.log("ZMath Auto Element interception contract: ok");
