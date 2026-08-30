import { NextResponse, type NextRequest } from "next/server";

import { getDb } from "@/lib/db";
import { logError, toApiError } from "@/lib/errors";
import { parsePaginationParams, getOffset, buildPaginatedResponse } from "@/lib/pagination";
import { getReadOnlyHeaders } from "@/lib/readonly";
import type { LevelPoint } from "@/lib/types";

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
      "select count(*)::text as count from levels",
    );
    const total = Number(countResult.rows[0]?.count ?? 0);

    // Get paginated results
    const result = await db.query<{
      uuid: string;
      value: number;
      exp: number;
      members_count: string;
    }>(
      `
      select
        l.uuid::text as uuid,
        l.value,
        l.exp,
        count(m.uuid)::text as members_count
      from levels l
      left join members m on m.level_uuid = l.uuid
      group by l.uuid
      order by l.value asc
      limit $1 offset $2
      `,
      [params.limit, getOffset(params.page, params.limit)],
    );

    const levels: LevelPoint[] = result.rows.map((row) => ({
      uuid: row.uuid,
      value: row.value,
      exp: row.exp,
      membersCount: Number(row.members_count),
    }));

    const response = buildPaginatedResponse(levels, params.page, params.limit, total);
    return NextResponse.json(response, { headers: getReadOnlyHeaders() });
  } catch (error) {
    logError(error, "GET /api/levels");
    return NextResponse.json(toApiError(error, "Failed to fetch levels"), { status: 500, headers: getReadOnlyHeaders() });
  }
}
