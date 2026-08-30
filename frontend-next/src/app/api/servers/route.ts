import { NextResponse, type NextRequest } from "next/server";

import { getDb } from "@/lib/db";
import { AppError, logError, toApiError } from "@/lib/errors";
import { parsePaginationParams, getOffset, buildPaginatedResponse } from "@/lib/pagination";
import { getReadOnlyHeaders } from "@/lib/readonly";
import type { ServerSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  // Enforce read-only
  if (request.method !== "GET") {
    return NextResponse.json(
      toApiError(new Error("Method not allowed"), "Only GET requests are allowed"),
      { status: 405, headers: getReadOnlyHeaders() },
    );
  }
  try {
    const params = parsePaginationParams(
      Object.fromEntries(request.nextUrl.searchParams),
    );

    const db = getDb();

    // Get total count
    const countResult = await db.query<{ count: string }>(
      "select count(*)::text as count from servers",
    );
    const total = Number(countResult.rows[0]?.count ?? 0);

    // Get paginated results
    const result = await db.query<{
      uuid: string;
      name: string;
      last_seen: Date | null;
      members_count: string;
    }>(
      `
      select
        s.uuid::text as uuid,
        s.name,
        s.last_seen,
        count(m.uuid)::text as members_count
      from servers s
      left join members m on m.server_uuid = s.uuid
      group by s.uuid
      order by s.name asc
      limit $1 offset $2
      `,
      [params.limit, getOffset(params.page, params.limit)],
    );

    const servers: ServerSummary[] = result.rows.map((row) => ({
      uuid: row.uuid,
      name: row.name,
      lastSeen: row.last_seen ? row.last_seen.toISOString() : null,
      membersCount: Number(row.members_count),
    }));

    const response = buildPaginatedResponse(servers, params.page, params.limit, total);
    return NextResponse.json(response, { headers: getReadOnlyHeaders() });
  } catch (error) {
    logError(error, "GET /api/servers");
    return NextResponse.json(toApiError(error, "Failed to fetch servers"), { status: 500, headers: getReadOnlyHeaders() });
  }
}
