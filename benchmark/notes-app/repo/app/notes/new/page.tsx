import Header from "@/app/components/Header";
import NoteForm from "@/app/components/NoteForm";
import { createNoteAction } from "@/app/notes/actions";
import { requireUser } from "@/lib/auth";

export default async function NewNotePage() {
  const user = await requireUser();
  return (
    <main className="container">
      <Header email={user.email} />
      <h2>New note</h2>
      <NoteForm action={createNoteAction} submitLabel="Create note" />
    </main>
  );
}
