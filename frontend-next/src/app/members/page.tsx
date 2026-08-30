"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";

import type { MemberWithServer } from "@/app/api/members/route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type MembersResponse = {
  data: MemberWithServer[];
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
};

export default function MembersPage() {
  const [members, setMembers] = useState<MemberWithServer[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(50);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/members?page=${page}&limit=${limit}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Request failed with ${res.status}`);
        }
        return res.json() as Promise<MembersResponse>;
      })
      .then((data) => {
        setMembers(data.data);
        setTotal(data.total);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => setLoading(false));
  }, [page, limit]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return members;
    return members.filter(
      (member) =>
        member.player.name.toLowerCase().includes(term) ||
        member.server.name.toLowerCase().includes(term),
    );
  }, [members, search]);

  const totalPages = Math.ceil(total / limit);
  const hasNext = page < totalPages;
  const hasPrev = page > 1;

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-6 flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight">Members</h1>
        <p className="text-muted-foreground">Players tracked across all servers.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search</CardTitle>
          <Input
            placeholder="Filter by player or server name"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="max-w-sm"
          />
        </CardHeader>
        <CardContent>
          {error ? <p className="text-destructive">{error}</p> : null}
          {loading ? <p className="text-muted-foreground">Loading members...</p> : null}
          {!loading && !error && filtered.length === 0 ? (
            <p className="text-muted-foreground">No members found.</p>
          ) : null}

          {filtered.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Player</TableHead>
                    <TableHead>Server</TableHead>
                    <TableHead>Level</TableHead>
                    <TableHead>Exp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((member) => (
                    <TableRow key={member.uuid}>
                      <TableCell className="font-medium">{member.player.name}</TableCell>
                      <TableCell>
                        <Link
                          href={`/servers/${member.server.uuid}`}
                          className="text-primary hover:underline"
                        >
                          {member.server.name}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          Lvl {member.level ? member.level.value : 0}
                        </Badge>
                      </TableCell>
                      <TableCell>{member.exp}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {totalPages > 1 ? (
                <div className="mt-6 flex items-center justify-between border-t pt-4">
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
            </>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
