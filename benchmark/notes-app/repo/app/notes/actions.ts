"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireUser } from "@/lib/auth";
import * as notes from "@/lib/notes";

export type NoteFormState = { error?: string };

function readNoteForm(formData: FormData) {
  return {
    title: String(formData.get("title") ?? "").trim(),
    body: String(formData.get("body") ?? ""),
    tags: notes.parseTags(String(formData.get("tags") ?? "")),
  };
}

function validate(input: { title: string; body: string }): string | undefined {
  if (!input.title) return "Title is required.";
  if (input.title.length > notes.MAX_TITLE) return `Title must be at most ${notes.MAX_TITLE} characters.`;
  if (input.body.length > notes.MAX_BODY) return "Note is too long.";
}

function readId(formData: FormData): number {
  const id = Number(formData.get("id"));
  return Number.isInteger(id) && id > 0 ? id : 0;
}

export async function createNoteAction(_prev: NoteFormState, formData: FormData): Promise<NoteFormState> {
  const user = await requireUser();
  const input = readNoteForm(formData);
  const error = validate(input);
  if (error) return { error };
  const id = notes.createNote(user.id, input);
  revalidatePath("/notes");
  redirect(`/notes/${id}`);
}

export async function updateNoteAction(_prev: NoteFormState, formData: FormData): Promise<NoteFormState> {
  const user = await requireUser();
  const id = readId(formData);
  const input = readNoteForm(formData);
  const error = validate(input);
  if (error) return { error };
  if (!notes.updateNote(user.id, id, input)) return { error: "Note not found." };
  revalidatePath("/notes");
  redirect("/notes");
}

export async function deleteNoteAction(formData: FormData): Promise<void> {
  const user = await requireUser();
  notes.deleteNote(user.id, readId(formData));
  revalidatePath("/notes");
  redirect("/notes");
}

export async function setSharingAction(formData: FormData): Promise<void> {
  const user = await requireUser();
  const id = readId(formData);
  notes.setSharing(user.id, id, formData.get("enabled") === "true");
  revalidatePath(`/notes/${id}`);
}
