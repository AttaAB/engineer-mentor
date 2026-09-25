import { headers } from "next/headers";
import { notFound } from "next/navigation";
import Header from "@/app/components/Header";
import NoteForm from "@/app/components/NoteForm";
import { deleteNoteAction, setSharingAction, updateNoteAction } from "@/app/notes/actions";
import { requireUser } from "@/lib/auth";
import { getNote } from "@/lib/notes";

type Props = { params: Promise<{ id: string }> };

async function baseUrl(): Promise<string> {
  if (process.env.APP_URL) return process.env.APP_URL.replace(/\/$/, "");
  const h = await headers();
  const host = h.get("x-forwarded-host") ?? h.get("host") ?? "localhost:3000";
  const proto = h.get("x-forwarded-proto") ?? "http";
  return `${proto}://${host}`;
}

export default async function EditNotePage({ params }: Props) {
  const user = await requireUser();
  const id = Number((await params).id);
  const note = Number.isInteger(id) ? getNote(user.id, id) : null;
  if (!note) notFound();
  const shareUrl = note.shareToken ? `${await baseUrl()}/s/${note.shareToken}` : null;

  return (
    <main className="container">
      <Header email={user.email} />
      <h2>Edit note</h2>
      <NoteForm key={note.updatedAt} action={updateNoteAction} note={note} submitLabel="Save" />

      <section className="card">
        <h2>Sharing</h2>
        {shareUrl ? (
          <>
            <p>Anyone with this link can read this note:</p>
            <p><a href={shareUrl} target="_blank" rel="noreferrer">{shareUrl}</a></p>
            <form action={setSharingAction}>
              <input type="hidden" name="id" value={note.id} />
              <input type="hidden" name="enabled" value="false" />
              <button type="submit" className="secondary">Stop sharing</button>
            </form>
          </>
        ) : (
          <form action={setSharingAction} className="row">
            <input type="hidden" name="id" value={note.id} />
            <input type="hidden" name="enabled" value="true" />
            <span className="muted">This note is private.</span>
            <button type="submit" className="secondary">Create public link</button>
          </form>
        )}
      </section>

      <form action={deleteNoteAction}>
        <input type="hidden" name="id" value={note.id} />
        <button type="submit" className="danger">Delete note</button>
      </form>
    </main>
  );
}
