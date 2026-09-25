import "server-only";
import crypto from "node:crypto";
import { getDb } from "./db";

export type Note = {
  id: number;
  title: string;
  body: string;
  tags: string[];
  shareToken: string | null;
  createdAt: number;
  updatedAt: number;
};

type NoteRow = {
  id: number;
  title: string;
  body: string;
  share_token: string | null;
  created_at: number;
  updated_at: number;
  tags: string | null;
};

export const MAX_TITLE = 200;
export const MAX_BODY = 100_000;
const MAX_TAGS = 20;
const MAX_TAG_LEN = 40;

const SELECT_NOTE = `
  SELECT n.id, n.title, n.body, n.share_token, n.created_at, n.updated_at,
         (SELECT group_concat(tag, char(31)) FROM (SELECT tag FROM note_tags WHERE note_id = n.id ORDER BY tag)) AS tags
  FROM notes n`;

function toNote(row: NoteRow): Note {
  return {
    id: row.id,
    title: row.title,
    body: row.body,
    tags: row.tags ? row.tags.split("\u001f") : [],
    shareToken: row.share_token,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

/** Turns "Work, ideas ,work" into ["ideas", "work"]. */
export function parseTags(input: string): string[] {
  const tags = input
    .split(",")
    .map((t) => t.trim().toLowerCase().replace(/\s+/g, "-").slice(0, MAX_TAG_LEN))
    .filter(Boolean);
  return [...new Set(tags)].slice(0, MAX_TAGS);
}

function escapeLike(s: string): string {
  return s.replace(/[\\%_]/g, (c) => "\\" + c);
}

export function listNotes(userId: number, opts: { q?: string; tag?: string } = {}): Note[] {
  const where = ["n.user_id = ?"];
  const params: unknown[] = [userId];
  const q = opts.q?.trim();
  if (q) {
    const like = `%${escapeLike(q)}%`;
    where.push(`(n.title LIKE ? ESCAPE '\\' OR n.body LIKE ? ESCAPE '\\'
      OR EXISTS (SELECT 1 FROM note_tags t WHERE t.note_id = n.id AND t.tag LIKE ? ESCAPE '\\'))`);
    params.push(like, like, like);
  }
  if (opts.tag) {
    where.push("EXISTS (SELECT 1 FROM note_tags t WHERE t.note_id = n.id AND t.tag = ?)");
    params.push(opts.tag);
  }
  const rows = getDb()
    .prepare(`${SELECT_NOTE} WHERE ${where.join(" AND ")} ORDER BY n.updated_at DESC, n.id DESC`)
    .all(...params) as NoteRow[];
  return rows.map(toNote);
}

export function listTags(userId: number): { tag: string; count: number }[] {
  return getDb()
    .prepare(
      `SELECT t.tag, COUNT(*) AS count FROM note_tags t JOIN notes n ON n.id = t.note_id
       WHERE n.user_id = ? GROUP BY t.tag ORDER BY t.tag`,
    )
    .all(userId) as { tag: string; count: number }[];
}

export function getNote(userId: number, id: number): Note | null {
  const row = getDb().prepare(`${SELECT_NOTE} WHERE n.id = ? AND n.user_id = ?`).get(id, userId) as
    | NoteRow
    | undefined;
  return row ? toNote(row) : null;
}

export function getSharedNote(token: string): Note | null {
  const row = getDb().prepare(`${SELECT_NOTE} WHERE n.share_token = ?`).get(token) as NoteRow | undefined;
  return row ? toNote(row) : null;
}

function setTags(noteId: number, tags: string[]) {
  const db = getDb();
  db.prepare("DELETE FROM note_tags WHERE note_id = ?").run(noteId);
  const insert = db.prepare("INSERT INTO note_tags (note_id, tag) VALUES (?, ?)");
  for (const tag of tags) insert.run(noteId, tag);
}

export function createNote(userId: number, input: { title: string; body: string; tags: string[] }): number {
  const db = getDb();
  return db.transaction(() => {
    const now = Date.now();
    const info = db
      .prepare("INSERT INTO notes (user_id, title, body, created_at, updated_at) VALUES (?, ?, ?, ?, ?)")
      .run(userId, input.title, input.body, now, now);
    const id = Number(info.lastInsertRowid);
    setTags(id, input.tags);
    return id;
  })();
}

/** Returns false if the note doesn't exist or isn't owned by the user. */
export function updateNote(
  userId: number,
  id: number,
  input: { title: string; body: string; tags: string[] },
): boolean {
  const db = getDb();
  return db.transaction(() => {
    const info = db
      .prepare("UPDATE notes SET title = ?, body = ?, updated_at = ? WHERE id = ? AND user_id = ?")
      .run(input.title, input.body, Date.now(), id, userId);
    if (info.changes === 0) return false;
    setTags(id, input.tags);
    return true;
  })();
}

export function deleteNote(userId: number, id: number): boolean {
  return getDb().prepare("DELETE FROM notes WHERE id = ? AND user_id = ?").run(id, userId).changes > 0;
}

/** Enables sharing (new random token) or disables it (token cleared, old links stop working). */
export function setSharing(userId: number, id: number, enabled: boolean): boolean {
  const token = enabled ? crypto.randomBytes(18).toString("base64url") : null;
  return (
    getDb().prepare("UPDATE notes SET share_token = ? WHERE id = ? AND user_id = ?").run(token, id, userId)
      .changes > 0
  );
}
