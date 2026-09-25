import Link from "next/link";
import Header from "@/app/components/Header";
import { requireUser } from "@/lib/auth";
import { listNotes, listTags } from "@/lib/notes";

type Props = { searchParams: Promise<{ q?: string; tag?: string }> };

export default async function NotesPage({ searchParams }: Props) {
  const user = await requireUser();
  const { q = "", tag = "" } = await searchParams;
  const notes = listNotes(user.id, { q, tag: tag || undefined });
  const tags = listTags(user.id);

  return (
    <main className="container">
      <Header email={user.email} />
      <div className="row" style={{ marginBottom: 16 }}>
        <form className="row" style={{ flex: 1 }}>
          <input type="search" name="q" defaultValue={q} placeholder="Search notes" style={{ flex: 1 }} />
          {tag && <input type="hidden" name="tag" value={tag} />}
          <button type="submit" className="secondary">Search</button>
        </form>
        <Link href="/notes/new" className="button">New note</Link>
      </div>

      {tags.length > 0 && (
        <p>
          {tags.map((t) => (
            <Link
              key={t.tag}
              className="tag"
              href={{ pathname: "/notes", query: { ...(q ? { q } : {}), tag: t.tag } }}
              style={t.tag === tag ? { background: "#2456c7", color: "#fff" } : undefined}
            >
              {t.tag} ({t.count})
            </Link>
          ))}
          {tag && <Link href={{ pathname: "/notes", query: q ? { q } : {} }} className="muted">clear tag</Link>}
        </p>
      )}

      {notes.length === 0 ? (
        <p className="muted">{q || tag ? "No notes match." : "No notes yet. Create your first one."}</p>
      ) : (
        notes.map((n) => (
          <article key={n.id} className="card">
            <h2><Link href={`/notes/${n.id}`}>{n.title}</Link></h2>
            <p className="muted" style={{ margin: "0 0 6px" }}>
              Updated {new Date(n.updatedAt).toLocaleString()}
              {n.shareToken && " · shared"}
            </p>
            {n.body && <p style={{ margin: "0 0 6px" }}>{n.body.slice(0, 200)}{n.body.length > 200 && "..."}</p>}
            {n.tags.map((t) => <span key={t} className="tag">{t}</span>)}
          </article>
        ))
      )}
    </main>
  );
}
