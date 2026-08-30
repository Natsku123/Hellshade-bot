"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import type { LevelPoint, ServerDetail } from "@/lib/types";
import { MemberCard } from "@/components/member-card";

type LevelsResponse = {
  data: LevelPoint[];
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
};

export default function ServerDetailPage() {
  const params = useParams<{ id: string }>();
  const [server, setServer] = useState<ServerDetail | null>(null);
  const [levels, setLevels] = useState<LevelPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) {
      return;
    }

    // Fetch server details
    fetch(`/api/servers/${params.id}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Request failed with ${res.status}`);
        }
        return res.json() as Promise<ServerDetail>;
      })
      .then((data) => setServer(data))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown error");
      });

    // Fetch levels with pagination (first 500 should be enough for most cases)
    fetch("/api/levels?page=1&limit=500")
      .then((res) => (res.ok ? res.json() : { data: [] }))
      .then((data: LevelsResponse) => setLevels(data.data ?? []))
      .catch(() => setLevels([]));
  }, [params.id]);

  const nextLevelFor = (value: number) =>
    levels.find((level) => level.value === value + 1) ?? null;

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      {error ? <p className="text-destructive">{error}</p> : null}
      {!server && !error ? <p className="text-muted-foreground">Loading...</p> : null}

      {server ? (
        <div className="flex flex-col gap-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{server.name}</h1>
            <p className="text-muted-foreground">
              Last seen: {server.lastSeen ? new Date(server.lastSeen).toLocaleString() : "Never"}
            </p>
            <p className="text-muted-foreground">Members: {server.members.length}</p>
          </div>

          <section>
            <h2 className="mb-3 text-xl font-semibold">Top 10</h2>
            {server.top10.length === 0 ? (
              <p className="text-muted-foreground">No members yet.</p>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {server.top10.map((member) => (
                  <MemberCard
                    key={`top-${member.uuid}`}
                    member={member}
                    nextLevel={member.level ? nextLevelFor(member.level.value) : nextLevelFor(0)}
                  />
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="mb-3 text-xl font-semibold">All Members</h2>
            {server.members.length === 0 ? (
              <p className="text-muted-foreground">No members yet.</p>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {server.members.map((member) => (
                  <MemberCard
                    key={member.uuid}
                    member={member}
                    nextLevel={member.level ? nextLevelFor(member.level.value) : nextLevelFor(0)}
                  />
                ))}
              </div>
            )}
          </section>
        </div>
      ) : null}
    </div>
  );
}
