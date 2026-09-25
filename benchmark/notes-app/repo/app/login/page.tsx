import { redirect } from "next/navigation";
import AuthForm from "@/app/components/AuthForm";
import { login } from "@/app/auth-actions";
import { getCurrentUser } from "@/lib/auth";

export default async function LoginPage() {
  if (await getCurrentUser()) redirect("/notes");
  return <AuthForm mode="login" action={login} />;
}
