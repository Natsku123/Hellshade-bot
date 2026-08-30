"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import type { LevelPoint } from "@/lib/types";
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
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

type LevelsResponse = {
  data: LevelPoint[];
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
};

export default function LevelsPage() {
  const [levels, setLevels] = useState<LevelPoint[]>([]);
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
    fetch(`/api/levels?page=${page}&limit=${limit}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Request failed with ${res.status}`);
        }
        return res.json() as Promise<LevelsResponse>;
      })
      .then((data) => {
        setLevels(data.data);
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
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-6 flex flex-col gap-2">
        <h1 className="text-2xl font-bold tracking-tight">Levels</h1>
        <p className="text-muted-foreground">Level progression data.</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-end justify-between gap-4">
          <CardTitle>Level table</CardTitle>
          <div className="flex flex-col gap-1">
            <Label htmlFor="levels-limit" className="text-xs text-muted-foreground">
              Per page
            </Label>
            <Input
              id="levels-limit"
              type="number"
              min={1}
              max={500}
              value={limit}
              onChange={(event) => {
                setLimit(Number(event.target.value));
                setPage(1);
              }}
              className="w-24"
            />
          </div>
        </CardHeader>
        <CardContent>
          {error ? <p className="text-destructive">{error}</p> : null}
          {loading ? <p className="text-muted-foreground">Loading levels...</p> : null}
          {!loading && !error && levels.length === 0 ? (
            <p className="text-muted-foreground">No level data found.</p>
          ) : null}

          {levels.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Level</TableHead>
                    <TableHead>Experience Needed</TableHead>
                    <TableHead>Players</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {levels.map((level) => (
                    <TableRow key={level.uuid}>
                      <TableCell>{level.value}</TableCell>
                      <TableCell>{level.exp}</TableCell>
                      <TableCell>{level.membersCount}</TableCell>
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
