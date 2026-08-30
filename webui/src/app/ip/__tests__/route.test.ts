import { describe, expect, it } from "vitest";

import { GET } from "@/app/ip/route";

describe("GET /ip", () => {
  it("returns a PNG for the forwarded client address", () => {
    const response = GET(
      new Request("http://localhost/ip", { headers: { "x-forwarded-for": "203.0.113.1" } }),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("image/png");
  });

  it("prefers x-real-ip over x-forwarded-for", () => {
    const response = GET(
      new Request("http://localhost/ip", {
        headers: { "x-forwarded-for": "203.0.113.1", "x-real-ip": "198.51.100.1" },
      }),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("image/png");
  });
});