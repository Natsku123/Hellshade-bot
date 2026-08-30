import { NextResponse } from "next/server";

import { getDb } from "@/lib/db";
import { logError, toApiError } from "@/lib/errors";
import { getReadOnlyHeaders } from "@/lib/readonly";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  // Enforce read-only
  if (request.method !== "GET") {
    return NextResponse.json(
      toApiError(new Error("Method not allowed"), "Only GET requests are allowed"),
      { status: 405, headers: getReadOnlyHeaders() },
    );
  }

  try {
    const db = getDb();
    await db.query("select 1");
    return NextResponse.json({ ok: true, readonly: true }, { headers: getReadOnlyHeaders() });
  } catch (error) {
    logError(error, "GET /api/health");
    return NextResponse.json(
      {
        ok: false,
        readonly: true,
        ...toApiError(error, "Database connection failed"),
      },
      { status: 500, headers: getReadOnlyHeaders() },
    );
  }
}
