# webhook-api

Express + TypeScript service that receives payment webhooks (Stripe-style
`payment_intent.succeeded`), records payments in SQLite, and emails the
customer a confirmation.

## Run locally

```sh
npm install
cp .env.example .env
npm run dev                 # or: npm run build && npm start
npm run send-webhook        # in another terminal
curl -H 'Authorization: Bearer local-dev-token' \
  http://localhost:3000/customers/cus_demo123/payments
```

With `SMTP_URL` empty, emails are printed to the server console.

`send-webhook` options: `--event <id>` (send the same id twice to see dedupe),
`--customer`, `--email`, `--amount` (minor units), `--currency`, `--bad-signature`, `--url`.

## Endpoints

- `POST /webhooks/payments` - requires a valid `Stripe-Signature` header
  (`t=<ts>,v1=<hmac-sha256 of "<ts>.<raw body>">`, 5 minute tolerance).
  Returns 200 for new and duplicate events; other event types are acknowledged and ignored.
- `GET /customers/:customerId/payments?limit=20&before=<id>` - requires
  `Authorization: Bearer $API_TOKEN`. Newest first; pass `nextBefore` as `before` for the next page.
- `GET /health`

## Design notes

- Amounts are stored as integers in minor units (cents), as the provider sends them.
- Event ids and payment ids are unique in the database, so provider retries never double-record.
- The event and payment are written in one transaction. Emails are queued in
  the `payments` row (`email_status`) and sent after the webhook responds, with
  retries (up to 5 attempts, every 30s), so a mail outage never fails or delays the webhook.
- Payments with no customer email are stored with `email_status = 'skipped'`.
