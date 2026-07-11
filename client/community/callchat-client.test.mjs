import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const shell = await readFile(new URL("./callchat-shell.js", import.meta.url), "utf8");
const css = await readFile(new URL("./callchat-shell.css", import.meta.url), "utf8");
const config = JSON.parse(await readFile(new URL("./config.community.json", import.meta.url), "utf8"));
const profile = JSON.parse(await readFile(new URL("./client-profile.community.json", import.meta.url), "utf8"));
const home = await readFile(new URL("./home.html", import.meta.url), "utf8");

assert.equal(config.brand, "CallChat Community");
assert.equal(config.force_verification, true);
assert.equal(config.features.feature_group_calls, true);
assert.equal(config.features.feature_disable_call_per_sender_encryption, false);
assert.equal(config.default_server_config["m.homeserver"].server_name, "callchat.org");
assert.match(config.branding.auth_header_logo_url, /zmath-shield-logo\.svg$/);
assert.match(config.embedded_pages.home_url, /callchat-home\.html$/);
assert.equal(profile.edition, "community");
assert.match(shell, /callchat-command-bar/);
assert.match(shell, /client-profile\.json/);
assert.doesNotMatch(shell, /apiKey|password|access_token/i);
assert.match(css, /@media \(max-width: 760px\)/);
assert.match(home, /Matrix-compatible/);

console.log("CallChat Community client distribution contract: ok");
