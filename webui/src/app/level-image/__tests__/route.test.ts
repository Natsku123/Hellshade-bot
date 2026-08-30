import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/level-image/route";

describe("GET /level-image", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(new ArrayBuffer(0))));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns a PNG using the legacy query defaults", async () => {
    const response = await GET(new Request("http://localhost/level-image"));

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("image/png");
  });

  it("accepts legacy level image query parameters", async () => {
    const response = await GET(
      new Request(
        "http://localhost/level-image?name=Alice&current_exp=500&needed_exp=1000&level=4",
      ),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("image/png");
  });
});