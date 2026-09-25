import nodemailer, { type Transporter } from "nodemailer";
import type { Db, PaymentRow } from "./db.js";

export interface Mailer {
  send(to: string, subject: string, text: string): Promise<void>;
}

export function createMailer(smtpUrl: string | undefined, from: string): Mailer {
  if (!smtpUrl) {
    // Local development: print instead of sending.
    return {
      async send(to, subject, text) {
        console.log(`[email] to=${to} subject="${subject}"\n${text}\n`);
      },
    };
  }
  const transport: Transporter = nodemailer.createTransport(smtpUrl);
  return {
    async send(to, subject, text) {
      await transport.sendMail({ from, to, subject, text });
    },
  };
}

export function formatAmount(amount: number, currency: string): string {
  try {
    const formatter = new Intl.NumberFormat("en-US", { style: "currency", currency: currency.toUpperCase() });
    const digits = formatter.resolvedOptions().maximumFractionDigits ?? 2;
    return formatter.format(amount / 10 ** digits);
  } catch {
    return `${amount} ${currency.toUpperCase()} (minor units)`;
  }
}

function confirmationEmail(payment: PaymentRow) {
  const amount = formatAmount(payment.amount, payment.currency);
  return {
    subject: `Payment received: ${amount}`,
    text: [
      "Thanks for your payment.",
      "",
      `Amount: ${amount}`,
      `Reference: ${payment.provider_payment_id}`,
      `Date: ${payment.created_at}`,
    ].join("\n"),
  };
}

/**
 * Sends confirmation emails for payments that still need one. Emails are
 * queued in the payments table (email_status) rather than sent inline, so a
 * slow or failing mail server never makes the webhook fail and a crash
 * between "payment saved" and "email sent" is retried instead of lost.
 */
export async function deliverPendingEmails(db: Db, mailer: Mailer, batchSize = 20): Promise<number> {
  let sent = 0;
  for (const payment of db.claimPendingEmails(batchSize)) {
    const { subject, text } = confirmationEmail(payment);
    try {
      await mailer.send(payment.customer_email!, subject, text);
      db.markEmailSent(payment.id);
      sent++;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`[email] failed for payment ${payment.id} (attempt ${payment.email_attempts}): ${message}`);
      db.markEmailFailed(payment.id, message);
    }
  }
  return sent;
}

export function startEmailWorker(db: Db, mailer: Mailer, intervalMs = 30_000) {
  let running = false;
  const run = async () => {
    if (running) return;
    running = true;
    try {
      await deliverPendingEmails(db, mailer);
    } catch (err) {
      console.error("[email] worker error", err);
    } finally {
      running = false;
    }
  };
  const timer = setInterval(run, intervalMs);
  timer.unref();
  return { kick: () => void run(), stop: () => clearInterval(timer) };
}
