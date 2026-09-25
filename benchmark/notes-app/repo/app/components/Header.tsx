import Link from "next/link";
import { logout } from "@/app/auth-actions";

export default function Header({ email }: { email: string }) {
  return (
    <header className="header">
      <h1><Link href="/notes" style={{ color: "inherit", textDecoration: "none" }}>Notes</Link></h1>
      <form action={logout} className="row">
        <span className="muted">{email}</span>
        <button type="submit" className="secondary">Log out</button>
      </form>
    </header>
  );
}
