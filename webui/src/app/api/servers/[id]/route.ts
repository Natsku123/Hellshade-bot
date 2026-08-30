import { NextResponse } from "next/server";

import { getDb } from "@/lib/db";
import { AppError, logError, toApiError } from "@/lib/errors";
import { validators } from "@/lib/validation";
import { getReadOnlyHeaders } from "@/lib/readonly";
import type { MemberView, ServerDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;

  try {
    // Validate ID is a UUID
    const idError = validators.isUUID(id);
    if (idError) {
      throw new AppError(idError, 400, "INVALID_ID");
    }

    const db = getDb();
    const serverResult = await db.query<{
      uuid: string;
      discord_id: string;
      name: string;
      channel: string | null;
      last_seen: Date | null;
    }>(
      `
      select
        s.uuid::text as uuid,
        s.discord_id,
        s.name,
        s.channel,
        s.last_seen
      from servers s
      where s.uuid::text = $1
      limit 1
      `,
      [id],
    );

    if (serverResult.rowCount === 0) {
      throw new AppError("Server not found", 404, "NOT_FOUND");
    }

    const membersResult = await db.query<{
      member_uuid: string;
      member_exp: number;
      player_uuid: string;
      player_name: string;
      player_hidden: boolean;
      level_uuid: string | null;
      level_value: number | null;
      level_exp: number | null;
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
        l.exp as level_exp
      from members m
      join players p on p.uuid = m.player_uuid
      left join levels l on l.uuid = m.level_uuid
      where m.server_uuid::text = $1
      order by p.name asc
      `,
      [id],
    );

    const members: MemberView[] = membersResult.rows
      .map((row) => ({
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
      }))
      .filter((member) => !member.player.hidden && member.player.name !== "UNKNOWN");

    const top10 = [...members]
      .sort((a, b) => {
        if (a.level === null && b.level !== null) {
          return 1;
        }
        if (a.level !== null && b.level === null) {
          return -1;
        }
        if (a.level === null && b.level === null) {
          return 0;
        }
        if (a.level!.value !== b.level!.value) {
          return b.level!.value - a.level!.value;
        }
        return b.exp - a.exp;
      })
      .slice(0, 10);

    const server = serverResult.rows[0];
    const payload: ServerDetail = {
      uuid: server.uuid,
      discordId: server.discord_id,
      name: server.name,
      channel: server.channel,
      lastSeen: server.last_seen ? server.last_seen.toISOString() : null,
      members,
      top10,
    };

    return NextResponse.json(payload, { headers: getReadOnlyHeaders() });
  } catch (error) {
    logError(error, `GET /api/servers/[id]`);
    const apiError = toApiError(error, "Failed to fetch server");
    const statusCode = error instanceof AppError ? error.statusCode : 500;
    return NextResponse.json(apiError, { status: statusCode, headers: getReadOnlyHeaders() });
  }
}
