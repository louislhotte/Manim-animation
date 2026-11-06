import { db } from "../../../lib/db";

export async function GET() {
  const books = db
    .prepare("SELECT title, year FROM books ORDER BY year")
    .all();
  return Response.json(books);
}
