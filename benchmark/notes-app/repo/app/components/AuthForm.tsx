"use client";

import Link from "next/link";
import { useActionState } from "react";
import type { AuthState } from "@/app/auth-actions";

type Props = {
  mode: "login" | "signup";
  action: (prev: AuthState, formData: FormData) => Promise<AuthState>;
};

export default function AuthForm({ mode, action }: Props) {
  const [state, formAction, pending] = useActionState(action, {});
  const isLogin = mode === "login";
  return (
    <main className="container auth">
      <h1>{isLogin ? "Log in" : "Create an account"}</h1>
      <form action={formAction} className="stack card">
        <label>
          Email
          <input name="email" type="email" required autoComplete="email" defaultValue={state.email} />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            required
            minLength={isLogin ? undefined : 8}
            autoComplete={isLogin ? "current-password" : "new-password"}
          />
        </label>
        {state.error && <p className="error" role="alert">{state.error}</p>}
        <button type="submit" disabled={pending}>
          {pending ? "Please wait..." : isLogin ? "Log in" : "Sign up"}
        </button>
      </form>
      <p className="muted">
        {isLogin ? (
          <>No account? <Link href="/signup">Sign up</Link></>
        ) : (
          <>Already have an account? <Link href="/login">Log in</Link></>
        )}
      </p>
    </main>
  );
}
