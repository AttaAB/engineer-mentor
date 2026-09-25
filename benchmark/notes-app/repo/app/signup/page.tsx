import { redirect } from "next/navigation";
import AuthForm from "@/app/components/AuthForm";
import { signup } from "@/app/auth-actions";
import { getCurrentUser } from "@/lib/auth";

export default async function SignupPage() {
  if (await getCurrentUser()) redirect("/notes");
  return <AuthForm mode="signup" action={signup} />;
}
