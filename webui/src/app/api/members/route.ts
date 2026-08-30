import { NextResponse, type NextRequest } from "next/server";

import { getDb } from "@/lib/db";
import { logError, toApiError } from "@/lib/errors";
import { parsePaginationParams, getOffset, buildPaginatedResponse } from "@/lib/pagination";
import { getReadOnlyHeaders } from "@/lib/readonly";
import type { MemberView } from "@/lib/types";

export const dynamic = "force-dynamic";

export type MemberWithServer = MemberView & {
  server: { uuid: string; name: string };
};

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
    const countResult = await db.query<{ count: string }>(`
      select count(distinct m.uuid)::text as count
      from members m
      join players p on p.uuid = m.player_uuid
      where not p.hidden and p.name != 'UNKNOWN'
    `);
    const total = Number(countResult.rows[0]?.count ?? 0);

    // Get paginated results
    const result = await db.query<{
      member_uuid: string;
      member_exp: number;
      player_uuid: string;
      player_name: string;
      player_hidden: boolean;
      level_uuid: string | null;
      level_value: number | null;
      level_exp: number | null;
      server_uuid: string;
      server_name: string;
    }>(
      `
      select
        m.uuid::text as member_uuid,
        m.exp as member_exp,
        p.uuid::text as player_uuid,
        p.name as player_name,
        p.hidden as player_hidden,
        l.uuid::text as level_uuid,
        l.value as level_value,
        l.exp as level_exp,
        s.uuid::text as server_uuid,
        s.name as server_name
      from members m
      join players p on p.uuid = m.player_uuid
      join servers s on s.uuid = m.server_uuid
      left join levels l on l.uuid = m.level_uuid
      where not p.hidden and p.name != 'UNKNOWN'
      order by p.name asc
      limit $1 offset $2
      `,
      [params.limit, getOffset(params.page, params.limit)],
    );

    const members: MemberWithServer[] = result.rows.map((row) => ({
      uuid: row.member_uuid,
      exp: row.member_exp,
      player: {
        uuid: row.player_uuid,
        name: row.player_name,
        hidden: row.player_hidden,
      },
      level:
        row.level_uuid && row.level_value !== null && row.level_exp !== null
          ? {
              uuid: row.level_uuid,
              value: row.level_value,
              exp: row.level_exp,
            }
          : null,
      server: {
        uuid: row.server_uuid,
        name: row.server_name,
      },
    }));

    const response = buildPaginatedResponse(members, params.page, params.limit, total);
    return NextResponse.json(response, { headers: getReadOnlyHeaders() });
  } catch (error) {
    logError(error, "GET /api/members");
    return NextResponse.json(toApiError(error, "Failed to fetch members"), { status: 500, headers: getReadOnlyHeaders() });
  }
}
