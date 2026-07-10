export const FORMAT = "ZME1";
export const VERSION = 1;
export const PROFILE = "ZSHIELD-PBKDF2-AESGCM-1";
export const ITERATIONS = 600000;
export const MAX_ITERATIONS = 1200000;
export const MAX_PAYLOAD_BYTES = 50 * 1024 * 1024;

const encoder = new TextEncoder();

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
  const encoded = String(value || "");
  if (!encoded || encoded.length % 4 !== 0 || !/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)) {
    throw new Error("The ZME1 container contains malformed Base64 data.");
  }
  const binary = atob(encoded);
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

export function canonical(value) {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value && typeof value === "object") {
    return "{" + Object.keys(value).sort().map((key) => JSON.stringify(key) + ":" + canonical(value[key])).join(",") + "}";
  }
  return JSON.stringify(value);
}

async function patternDigest(patternBytes) {
  const source = patternBytes && patternBytes.length ? patternBytes : new Uint8Array();
  if (!source.length) return new Uint8Array(32);
  return new Uint8Array(await crypto.subtle.digest("SHA-256", source));
}

async function deriveKey(passphrase, patternBytes, salt, iterations) {
  if (String(passphrase || "").length < 14) {
    throw new Error("Use a passphrase with at least 14 characters.");
  }
  const pattern = await patternDigest(patternBytes);
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

function validateHeader(header) {
  if (!header || header.format !== FORMAT || header.version !== VERSION || header.profile !== PROFILE) {
    throw new Error("Unsupported or invalid ZME1 container.");
  }
  if (!header.payload || !header.kdf || !header.cipher) {
    throw new Error("The ZME1 header is incomplete.");
  }
  const iterations = Number(header.kdf.iterations);
  if (
    header.kdf.name !== "PBKDF2-SHA-256" ||
    !Number.isSafeInteger(iterations) ||
    iterations < ITERATIONS ||
    iterations > MAX_ITERATIONS
  ) {
    throw new Error("The container KDF profile is outside the supported bounds.");
  }
  if (header.cipher.name !== "AES-256-GCM" || Number(header.cipher.tagLength) !== 128) {
    throw new Error("The container cipher profile is unsupported.");
  }
  const payloadSize = Number(header.payload.size);
  if (!Number.isSafeInteger(payloadSize) || payloadSize < 0 || payloadSize > MAX_PAYLOAD_BYTES) {
    throw new Error("The container payload size is unsupported.");
  }
  if (base64ToBytes(header.kdf.salt).length !== 16 || base64ToBytes(header.cipher.iv).length !== 12) {
    throw new Error("The container salt or IV length is invalid.");
  }
}

export async function protectPayload(options) {
  const bytes = options.bytes instanceof Uint8Array ? options.bytes : new Uint8Array(options.bytes);
  if (bytes.length > MAX_PAYLOAD_BYTES) {
    throw new Error("Choose a payload no larger than 50 MB.");
  }
  const patternBytes = options.patternBytes || new Uint8Array();
  const salt = randomBytes(16);
  const iv = randomBytes(12);
  const header = {
    format: FORMAT,
    version: VERSION,
    profile: PROFILE,
    payload: {
      name: String(options.name || "payload.bin"),
      type: String(options.type || "application/octet-stream"),
      size: bytes.length,
      kind: String(options.kind || "file")
    },
    createdAt: options.createdAt || new Date().toISOString(),
    kdf: {
      name: "PBKDF2-SHA-256",
      iterations: ITERATIONS,
      salt: bytesToBase64(salt),
      patternRequired: patternBytes.length > 0
    },
    cipher: {
      name: "AES-256-GCM",
      iv: bytesToBase64(iv),
      tagLength: 128
    }
  };
  const key = await deriveKey(options.passphrase, patternBytes, salt, ITERATIONS);
  const ciphertext = new Uint8Array(await crypto.subtle.encrypt(
    {name: "AES-GCM", iv, additionalData: encoder.encode(canonical(header)), tagLength: 128},
    key,
    bytes
  ));
  return {header, ciphertext: bytesToBase64(ciphertext)};
}

export async function openContainerPayload(options) {
  const container = options.container;
  if (!container || !container.ciphertext) throw new Error("Unsupported or invalid ZME1 container.");
  const header = container.header;
  validateHeader(header);
  const patternBytes = options.patternBytes || new Uint8Array();
  if (header.kdf.patternRequired && !patternBytes.length) {
    throw new Error("This container requires the sender's pattern file.");
  }
  const ciphertext = base64ToBytes(container.ciphertext);
  if (ciphertext.length !== Number(header.payload.size) + 16) {
    throw new Error("Authenticated payload size does not match the header.");
  }
  const key = await deriveKey(
    options.passphrase,
    patternBytes,
    base64ToBytes(header.kdf.salt),
    Number(header.kdf.iterations)
  );
  let plaintext;
  try {
    plaintext = new Uint8Array(await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: base64ToBytes(header.cipher.iv),
        additionalData: encoder.encode(canonical(header)),
        tagLength: Number(header.cipher.tagLength)
      },
      key,
      ciphertext
    ));
  } catch (error) {
    throw new Error("Authentication failed. Check the passphrase, pattern file and container integrity.");
  }
  if (plaintext.length !== Number(header.payload.size)) {
    throw new Error("Authenticated payload size does not match the header.");
  }
  return {bytes: plaintext, header};
}
