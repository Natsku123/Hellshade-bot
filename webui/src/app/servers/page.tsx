"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Server as ServerIcon, ChevronLeft, ChevronRight } from "lucide-react";

import type { ServerSummary } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type ServersResponse = {
  data: ServerSummary[];
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
};

export default function ServersPage() {
  const [servers, setServers] = useState<ServerSummary[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(50);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    // Reset loading before each fetch; intentional, safe cascading re-render.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    fetch(`/api/servers?page=${page}&limit=${limit}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Request failed with ${res.status}`);
        }
        return res.json() as Promise<ServersResponse>;
      })
      .then((data) => {
        setServers(data.data);
        setTotal(data.total);
      })
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === "AbortError") return;
        setError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [page, limit]);

  const totalPages = Math.ceil(total / limit);
  const hasNext = page < totalPages;
  const hasPrev = page > 1;

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-6 flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight">Servers</h1>
        <p className="text-muted-foreground">Discord servers using Hellshade-bot.</p>
      </div>

      {error ? <p className="text-destructive">{error}</p> : null}
      {loading ? <p className="text-muted-foreground">Loading servers...</p> : null}
      {!loading && !error && servers.length === 0 ? (
        <p className="text-muted-foreground">No servers found.</p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {servers.map((server) => (
          <Link key={server.uuid} href={`/servers/${server.uuid}`}>
            <Card className="h-full transition-colors hover:border-primary">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ServerIcon className="size-4 text-primary" />
                  {server.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <Badge variant="secondary">{server.membersCount} members</Badge>
                <p className="text-sm text-muted-foreground">
                  Last seen: {server.lastSeen ? new Date(server.lastSeen).toLocaleString() : "Never"}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {totalPages > 1 ? (
        <div className="mt-8 flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Page {page} of {totalPages} ({total} total)
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={!hasPrev || loading}
            >
              <ChevronLeft className="size-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={!hasNext || loading}
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
