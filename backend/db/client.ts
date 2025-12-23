import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";

console.log("DATABASE_URL USED BY BACKEND:", process.env.DATABASE_URL);

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export const db = drizzle(pool);