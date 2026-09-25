import Database from "better-sqlite3";

export type EmailStatus = "pending" | "sending" | "sent" | "failed" | "skipped";

export interface PaymentRow {
  id: number;
  provider_payment_id: string;
  event_id: string;
  customer_id: string;
  customer_email: string | null;
  amount: number; // minor units (e.g. cents), never floats
  currency: string;
  status: string;
  email_status: EmailStatus;
  email_attempts: number;
  email_last_error: string | null;
  created_at: string;
}

export interface NewPayment {
  providerPaymentId: string;
  eventId: string;
  customerId: string;
  customerEmail: string | null;
  amount: number;
  currency: string;
  status: string;
}

export const MAX_EMAIL_ATTEMPTS = 5;

export function openDatabase(path: string) {
  const db = new Database(path);
  db.pragma("journal_mode = WAL");
  db.pragma("busy_timeout = 5000");

  db.exec(`
    CREATE TABLE IF NOT EXISTS webhook_events (
      event_id    TEXT PRIMARY KEY,
      type        TEXT NOT NULL,
      received_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    );

    CREATE TABLE IF NOT EXISTS payments (
      id                  INTEGER PRIMARY KEY AUTOINCREMENT,
      provider_payment_id TEXT NOT NULL UNIQUE,
      event_id            TEXT NOT NULL REFERENCES webhook_events(event_id),
      customer_id         TEXT NOT NULL,
      customer_email      TEXT,
      amount              INTEGER NOT NULL CHECK (amount >= 0),
      currency            TEXT NOT NULL,
      status              TEXT NOT NULL,
      email_status        TEXT NOT NULL DEFAULT 'pending',
      email_attempts      INTEGER NOT NULL DEFAULT 0,
      email_last_error    TEXT,
      created_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    );

    CREATE INDEX IF NOT EXISTS payments_customer_idx ON payments (customer_id, id DESC);
    CREATE INDEX IF NOT EXISTS payments_email_status_idx ON payments (email_status);
  `);

  // If the process died mid-send, put those rows back in the queue.
  db.prepare("UPDATE payments SET email_status = 'pending' WHERE email_status = 'sending'").run();

  const insertEvent = db.prepare("INSERT OR IGNORE INTO webhook_events (event_id, type) VALUES (?, ?)");
  const insertPayment = db.prepare(`
    INSERT INTO payments (provider_payment_id, event_id, customer_id, customer_email, amount, currency, status, email_status)
    VALUES (@providerPaymentId, @eventId, @customerId, @customerEmail, @amount, @currency, @status, @emailStatus)
    ON CONFLICT (provider_payment_id) DO NOTHING
  `);

  return {
    raw: db,

    /**
     * Records the event and its payment atomically. Returns false if the event
     * was already processed (providers retry deliveries, so duplicates are normal).
     */
    recordEvent: db.transaction((eventId: string, type: string, payment: NewPayment | null): boolean => {
      if (insertEvent.run(eventId, type).changes === 0) return false;
      if (payment) {
        insertPayment.run({ ...payment, emailStatus: payment.customerEmail ? "pending" : "skipped" });
      }
      return true;
    }),

    listCustomerPayments(customerId: string, limit: number, beforeId?: number): PaymentRow[] {
      return db
        .prepare(
          `SELECT * FROM payments
           WHERE customer_id = ? AND (? IS NULL OR id < ?)
           ORDER BY id DESC LIMIT ?`,
        )
        .all(customerId, beforeId ?? null, beforeId ?? null, limit) as PaymentRow[];
    },

    /** Atomically claims payments whose confirmation email still needs sending. */
    claimPendingEmails(limit: number): PaymentRow[] {
      return db
        .prepare(
          `UPDATE payments SET email_status = 'sending', email_attempts = email_attempts + 1
           WHERE id IN (
             SELECT id FROM payments
             WHERE email_status IN ('pending', 'failed') AND email_attempts < ?
             ORDER BY id LIMIT ?
           )
           RETURNING *`,
        )
        .all(MAX_EMAIL_ATTEMPTS, limit) as PaymentRow[];
    },

    markEmailSent(id: number): void {
      db.prepare("UPDATE payments SET email_status = 'sent', email_last_error = NULL WHERE id = ?").run(id);
    },

    markEmailFailed(id: number, error: string): void {
      db.prepare("UPDATE payments SET email_status = 'failed', email_last_error = ? WHERE id = ?").run(error, id);
    },

    close(): void {
      db.close();
    },
  };
}

export type Db = ReturnType<typeof openDatabase>;
