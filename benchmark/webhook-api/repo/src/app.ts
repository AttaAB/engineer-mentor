import express, { type NextFunction, type Request, type Response } from "express";
import { timingSafeEqual, createHash } from "node:crypto";
import { z } from "zod";
import type { Config } from "./config.js";
import type { Db, NewPayment, PaymentRow } from "./db.js";
import { verifySignature } from "./signature.js";

const eventSchema = z.object({
  id: z.string().min(1),
  type: z.string().min(1),
  data: z.object({ object: z.unknown() }),
});

// Subset of a Stripe PaymentIntent that we rely on.
const paymentIntentSchema = z.object({
  id: z.string().min(1),
  amount: z.number().int().nonnegative(),
  amount_received: z.number().int().nonnegative().optional(),
  currency: z.string().min(3).max(3),
  status: z.string(),
  customer: z.string().nullish(),
  receipt_email: z.string().email().nullish(),
  metadata: z.record(z.string(), z.string()).optional(),
});

const listQuerySchema = z.object({
  limit: z.coerce.number().int().min(1).max(100).default(20),
  before: z.coerce.number().int().positive().optional(),
});

function toPayment(eventId: string, object: unknown): NewPayment | { error: string } {
  const parsed = paymentIntentSchema.safeParse(object);
  if (!parsed.success) return { error: `invalid payment_intent: ${parsed.error.message}` };
  const pi = parsed.data;
  const customerId = pi.customer ?? pi.metadata?.customer_id;
  if (!customerId) return { error: "payment_intent has no customer" };
  return {
    providerPaymentId: pi.id,
    eventId,
    customerId,
    customerEmail: pi.receipt_email ?? pi.metadata?.email ?? null,
    amount: pi.amount_received ?? pi.amount,
    currency: pi.currency.toLowerCase(),
    status: pi.status,
  };
}

function serializePayment(row: PaymentRow) {
  return {
    id: row.id,
    providerPaymentId: row.provider_payment_id,
    customerId: row.customer_id,
    amount: row.amount,
    currency: row.currency,
    status: row.status,
    emailStatus: row.email_status,
    createdAt: row.created_at,
  };
}

function tokensEqual(a: string, b: string): boolean {
  // Hash first so lengths always match and timingSafeEqual does not throw.
  const ha = createHash("sha256").update(a).digest();
  const hb = createHash("sha256").update(b).digest();
  return timingSafeEqual(ha, hb);
}

export function createApp(config: Config, db: Db, onPaymentRecorded: () => void) {
  const app = express();
  app.disable("x-powered-by");

  app.get("/health", (_req, res) => {
    res.json({ ok: true });
  });

  // Raw body is required for signature verification; must not go through express.json().
  app.post("/webhooks/payments", express.raw({ type: "application/json", limit: "1mb" }), (req, res) => {
    const rawBody = req.body;
    if (!Buffer.isBuffer(rawBody)) {
      res.status(400).json({ error: "expected application/json body" });
      return;
    }
    if (!verifySignature(config.webhookSecret, rawBody, req.header("stripe-signature"))) {
      res.status(400).json({ error: "invalid signature" });
      return;
    }

    let json: unknown;
    try {
      json = JSON.parse(rawBody.toString("utf8"));
    } catch {
      res.status(400).json({ error: "invalid JSON" });
      return;
    }
    const event = eventSchema.safeParse(json);
    if (!event.success) {
      res.status(400).json({ error: "invalid event envelope" });
      return;
    }
    const { id: eventId, type } = event.data;

    let payment: NewPayment | null = null;
    if (type === "payment_intent.succeeded") {
      const result = toPayment(eventId, event.data.data.object);
      if ("error" in result) {
        console.warn(`[webhook] event ${eventId}: ${result.error}`);
        res.status(400).json({ error: result.error });
        return;
      }
      payment = result;
    }
    // Other event types are acknowledged (and recorded for dedupe) but otherwise ignored.

    const isNew = db.recordEvent(eventId, type, payment);
    res.status(200).json({ received: true, duplicate: !isNew });

    if (isNew && payment) onPaymentRecorded();
  });

  app.get("/customers/:customerId/payments", (req: Request, res: Response) => {
    const auth = req.header("authorization") ?? "";
    const token = auth.startsWith("Bearer ") ? auth.slice("Bearer ".length) : "";
    if (!token || !tokensEqual(token, config.apiToken)) {
      res.status(401).json({ error: "unauthorized" });
      return;
    }

    const query = listQuerySchema.safeParse(req.query);
    if (!query.success) {
      res.status(400).json({ error: "invalid query", details: query.error.issues });
      return;
    }
    const { limit, before } = query.data;
    const customerId = String(req.params.customerId);
    const rows = db.listCustomerPayments(customerId, limit, before);
    res.json({
      data: rows.map(serializePayment),
      nextBefore: rows.length === limit ? rows[rows.length - 1].id : null,
    });
  });

  app.use((_req, res) => {
    res.status(404).json({ error: "not found" });
  });

  app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
    const status = (err as { status?: number }).status;
    if (status && status >= 400 && status < 500) {
      res.status(status).json({ error: "bad request" });
      return;
    }
    console.error(err);
    res.status(500).json({ error: "internal error" });
  });

  return app;
}
