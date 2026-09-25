function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable ${name} (see .env.example)`);
  }
  return value;
}

export interface Config {
  port: number;
  databasePath: string;
  webhookSecret: string;
  apiToken: string;
  smtpUrl: string | undefined;
  emailFrom: string;
}

export function loadConfig(): Config {
  return {
    port: Number(process.env.PORT ?? 3000),
    databasePath: process.env.DATABASE_PATH ?? "./payments.db",
    webhookSecret: required("WEBHOOK_SECRET"),
    apiToken: required("API_TOKEN"),
    smtpUrl: process.env.SMTP_URL || undefined,
    emailFrom: process.env.EMAIL_FROM ?? "payments@example.com",
  };
}
