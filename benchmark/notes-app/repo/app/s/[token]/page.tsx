import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getSharedNote } from "@/lib/notes";

type Props = { params: Promise<{ token: string }> };

export const metadata: Metadata = { robots: { index: false, follow: false } };

export default async function SharedNotePage({ params }: Props) {
  const { token } = await params;
  const note = getSharedNote(token);
  if (!note) notFound();
  return (
    <main className="container">
      <article className="card">
        <h1 style={{ marginTop: 0 }}>{note.title}</h1>
        <p className="muted">Last updated {new Date(note.updatedAt).toLocaleString()}</p>
        <div className="note-body">{note.body}</div>
        {note.tags.length > 0 && <p>{note.tags.map((t) => <span key={t} className="tag">{t}</span>)}</p>}
      </article>
      <p className="muted">Shared read-only note.</p>
    </main>
  );
}
