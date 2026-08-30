import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";
import type { Pool } from "pg";

import { GET as getServers } from "@/app/api/servers/route";

// Mock the database
vi.mock("@/lib/db", () => ({
  getDb: vi.fn(),
}));

describe("GET /api/servers", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return paginated servers", async () => {
    const { getDb } = await import("@/lib/db");
    const mockQuery = vi.fn()
      .mockResolvedValueOnce({ rows: [{ count: "10" }] }) // count query
      .mockResolvedValueOnce({
        rows: [
          {
            uuid: "123",
            name: "Test Server",
            last_seen: new Date("2026-01-01"),
            members_count: "5",
          },
        ],
      }); // data query

    vi.mocked(getDb).mockReturnValue({
      query: mockQuery,
    } as unknown as Pool);

    const request = new NextRequest("http://localhost:3000/api/servers?page=1&limit=50");
    const response = await getServers(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.data).toHaveLength(1);
    expect(data.page).toBe(1);
    expect(data.limit).toBe(50);
    expect(data.total).toBe(10);
  });

  it("should handle database errors", async () => {
    const { getDb } = await import("@/lib/db");
    const mockQuery = vi.fn().mockRejectedValue(new Error("DB connection failed"));

    vi.mocked(getDb).mockReturnValue({
      query: mockQuery,
    } as unknown as Pool);

    const request = new NextRequest("http://localhost:3000/api/servers?page=1&limit=50");
    const response = await getServers(request);

    expect(response.status).toBe(500);
    const data = await response.json();
    expect(data.error).toBeDefined();
  });

  it("should validate pagination parameters", async () => {
    const { getDb } = await import("@/lib/db");
    const mockQuery = vi.fn()
      .mockResolvedValueOnce({ rows: [{ count: "100" }] })
      .mockResolvedValueOnce({ rows: [] });

    vi.mocked(getDb).mockReturnValue({
      query: mockQuery,
    } as unknown as Pool);

    // Test with invalid page (should default to 1)
    const request = new NextRequest("http://localhost:3000/api/servers?page=invalid&limit=50");
    const response = await getServers(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.page).toBe(1);
  });
});
