"use server";

import { redirect } from "next/navigation";
import { createUser, endSession, normalizeEmail, startSession, verifyCredentials } from "@/lib/auth";

export type AuthState = { error?: string; email?: string };

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function readForm(formData: FormData) {
  return {
    email: normalizeEmail(String(formData.get("email") ?? "")),
    password: String(formData.get("password") ?? ""),
  };
}

export async function signup(_prev: AuthState, formData: FormData): Promise<AuthState> {
  const { email, password } = readForm(formData);
  if (!EMAIL_RE.test(email) || email.length > 254) return { error: "Enter a valid email address.", email };
  if (password.length < 8) return { error: "Password must be at least 8 characters.", email };
  if (password.length > 72) return { error: "Password must be at most 72 characters.", email };

  const user = await createUser(email, password);
  if (!user) return { error: "An account with that email already exists.", email };
  await startSession(user.id);
  redirect("/notes");
}

export async function login(_prev: AuthState, formData: FormData): Promise<AuthState> {
  const { email, password } = readForm(formData);
  const user = await verifyCredentials(email, password);
  if (!user) return { error: "Invalid email or password.", email };
  await startSession(user.id);
  redirect("/notes");
}

export async function logout(): Promise<void> {
  await endSession();
  redirect("/login");
}
