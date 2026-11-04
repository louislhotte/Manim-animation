import { db } from "../../lib/db";

export const dynamic = "force-dynamic";

export default function Books() {
  const books = db
    .prepare("SELECT title, year FROM books ORDER BY year")
    .all();
  const at = new Date().toISOString();
  return (
    <main>
      <h1>Books</h1>
      <ul>
        {books.map((b) => (
          <li key={b.title}>{`${b.title} (${b.year})`}</li>
        ))}
      </ul>
      <p>{`rendered at ${at}`}</p>
    </main>
  );
}
