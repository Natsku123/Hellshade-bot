import { Pool } from "pg";

const buildConnectionString = (): string => {
  const fromUrl =
    process.env.DATABASE_URL ??
    process.env.DB_URL ??
    process.env.NEXT_DATABASE_URL;

  if (fromUrl) {
    return fromUrl;
  }

  const host = process.env.DB_HOST ?? "localhost";
  const user = process.env.DB_USER ?? "";
  const pass = process.env.DB_PASS ?? "";
  const name = process.env.DB_NAME ?? "";

  return `postgresql://${user}:${pass}@${host}/${name}`;
};

const connectionString = buildConnectionString();

const globalForPg = globalThis as unknown as {
  pgPool: Pool | undefined;
};

export const getDb = (): Pool => {
  if (!connectionString || connectionString === "postgresql://:@localhost/") {
    throw new Error(
      "Database connection is not configured. Set DATABASE_URL or DB_HOST/DB_USER/DB_PASS/DB_NAME.",
    );
  }

  if (!globalForPg.pgPool) {
    globalForPg.pgPool = new Pool({
      connectionString,
    });
  }

  return globalForPg.pgPool;
};
