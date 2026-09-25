"use client";

import { useActionState } from "react";
import type { NoteFormState } from "@/app/notes/actions";

type Props = {
  action: (prev: NoteFormState, formData: FormData) => Promise<NoteFormState>;
  note?: { id: number; title: string; body: string; tags: string[] };
  submitLabel: string;
};

export default function NoteForm({ action, note, submitLabel }: Props) {
  const [state, formAction, pending] = useActionState(action, {});
  return (
    <form action={formAction} className="stack card">
      {note && <input type="hidden" name="id" value={note.id} />}
      <label>
        Title
        <input name="title" required maxLength={200} defaultValue={note?.title} />
      </label>
      <label>
        Note
        <textarea name="body" defaultValue={note?.body} />
      </label>
      <label>
        Tags (comma separated)
        <input name="tags" placeholder="work, ideas" defaultValue={note?.tags.join(", ")} />
      </label>
      {state.error && <p className="error" role="alert">{state.error}</p>}
      <div className="row">
        <button type="submit" disabled={pending}>{pending ? "Saving..." : submitLabel}</button>
      </div>
    </form>
  );
}
