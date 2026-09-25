// Sends a signed, Stripe-shaped payment_intent.succeeded event to the local server.
//
//   npm run send-webhook                     # new random payment
//   npm run send-webhook -- --event evt_123  # reuse an event id to test dedupe
//   npm run send-webhook -- --bad-signature  # expect a 400
import { randomBytes } from "node:crypto";
import { signatureHeader } from "../src/signature.js";

try {
  process.loadEnvFile?.(".env");
} catch {
  // ignore
}

const args = process.argv.slice(2);
const flag = (name: string) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};

const url = flag("--url") ?? `http://localhost:${process.env.PORT ?? 3000}/webhooks/payments`;
const secret = process.env.WEBHOOK_SECRET;
if (!secret) {
  console.error("WEBHOOK_SECRET is not set (copy .env.example to .env)");
  process.exit(1);
}

const id = () => randomBytes(8).toString("hex");
const event = {
  id: flag("--event") ?? `evt_${id()}`,
  object: "event",
  type: "payment_intent.succeeded",
  created: Math.floor(Date.now() / 1000),
  data: {
    object: {
      id: flag("--payment") ?? `pi_${id()}`,
      object: "payment_intent",
      amount: Number(flag("--amount") ?? 2500),
      amount_received: Number(flag("--amount") ?? 2500),
      currency: flag("--currency") ?? "usd",
      status: "succeeded",
      customer: flag("--customer") ?? "cus_demo123",
      receipt_email: flag("--email") ?? "customer@example.com",
      metadata: {},
    },
  },
};

const body = JSON.stringify(event);
const signature = args.includes("--bad-signature") ? "t=0,v1=deadbeef" : signatureHeader(secret, body);

async function main() {
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json", "stripe-signature": signature },
    body,
  });
  console.log(`POST ${url} -> ${res.status}`);
  console.log(await res.text());
  console.log(`event=${event.id} payment=${event.data.object.id} customer=${event.data.object.customer}`);
  process.exitCode = res.ok ? 0 : 1;
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
