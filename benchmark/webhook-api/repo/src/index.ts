import { loadConfig } from "./config.js";
import { openDatabase } from "./db.js";
import { createMailer, startEmailWorker } from "./email.js";
import { createApp } from "./app.js";

try {
  process.loadEnvFile?.(".env");
} catch {
  // No .env file; rely on the real environment.
}

const config = loadConfig();
const db = openDatabase(config.databasePath);
const mailer = createMailer(config.smtpUrl, config.emailFrom);
const worker = startEmailWorker(db, mailer);
const app = createApp(config, db, worker.kick);

const server = app.listen(config.port, () => {
  console.log(`webhook-api listening on http://localhost:${config.port}`);
  worker.kick(); // flush anything left over from a previous run
});

function shutdown(signal: string) {
  console.log(`${signal} received, shutting down`);
  worker.stop();
  server.close(() => {
    db.close();
    process.exit(0);
  });
}
process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
