// Seed the demo SQLite database with real books (run before `next build`).
import { DatabaseSync } from "node:sqlite";
import { mkdirSync } from "node:fs";

mkdirSync("data", { recursive: true });
const db = new DatabaseSync("data/app.db");
db.exec("DROP TABLE IF EXISTS books");
db.exec("CREATE TABLE books (title TEXT PRIMARY KEY, year INTEGER)");
const ins = db.prepare("INSERT INTO books (title, year) VALUES (?, ?)");
for (const [title, year] of [
  ["The Mythical Man-Month", 1975],
  ["The C Programming Language", 1978],
  ["Structure and Interpretation of Computer Programs", 1985],
  ["Design Patterns", 1994],
  ["The Pragmatic Programmer", 1999],
]) {
  ins.run(title, year);
}
console.log("seeded", db.prepare("SELECT COUNT(*) AS n FROM books").get().n, "books");
