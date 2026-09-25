import { createHmac, timingSafeEqual } from "node:crypto";

// Stripe-compatible signature scheme:
//   Stripe-Signature: t=<unix seconds>,v1=<hex hmac-sha256 of "<t>.<raw body>">
// The HMAC must be computed over the exact raw bytes received, so the webhook
// route reads the body with express.raw() rather than express.json().

const DEFAULT_TOLERANCE_SECONDS = 300;

export function computeSignature(secret: string, timestamp: number, rawBody: Buffer | string): string {
  return createHmac("sha256", secret).update(`${timestamp}.`).update(rawBody).digest("hex");
}

export function signatureHeader(secret: string, rawBody: Buffer | string, timestamp = Math.floor(Date.now() / 1000)): string {
  return `t=${timestamp},v1=${computeSignature(secret, timestamp, rawBody)}`;
}

export function verifySignature(
  secret: string,
  rawBody: Buffer,
  header: string | undefined,
  toleranceSeconds = DEFAULT_TOLERANCE_SECONDS,
  now = Math.floor(Date.now() / 1000),
): boolean {
  if (!header) return false;

  let timestamp: number | undefined;
  const candidates: string[] = [];
  for (const part of header.split(",")) {
    const [key, value] = part.split("=", 2).map((s) => s.trim());
    if (key === "t") timestamp = Number(value);
    else if (key === "v1" && value) candidates.push(value);
  }
  if (timestamp === undefined || !Number.isFinite(timestamp) || candidates.length === 0) return false;

  // Reject old (or far-future) timestamps to limit replay of captured requests.
  if (Math.abs(now - timestamp) > toleranceSeconds) return false;

  const expected = Buffer.from(computeSignature(secret, timestamp, rawBody), "hex");
  return candidates.some((candidate) => {
    const given = Buffer.from(candidate, "hex");
    return given.length === expected.length && timingSafeEqual(given, expected);
  });
}
