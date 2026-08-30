import { describe, it, expect } from "vitest";
import { parsePaginationParams, getOffset, buildPaginatedResponse, validators } from "@/lib";

describe("Pagination Utilities", () => {
  it("should parse valid pagination parameters", () => {
    const params = parsePaginationParams({ page: "2", limit: "25" });
    expect(params.page).toBe(2);
    expect(params.limit).toBe(25);
  });

  it("should use defaults for invalid parameters", () => {
    const params = parsePaginationParams({});
    expect(params.page).toBe(1);
    expect(params.limit).toBe(50);
  });

  it("should clamp limit to maximum", () => {
    const params = parsePaginationParams({ limit: "9999" });
    expect(params.limit).toBe(500);
  });

  it("should ensure page is at least 1", () => {
    const params = parsePaginationParams({ page: "-5" });
    expect(params.page).toBe(1);
  });

  it("should calculate correct offset", () => {
    expect(getOffset(1, 50)).toBe(0);
    expect(getOffset(2, 50)).toBe(50);
    expect(getOffset(3, 25)).toBe(50);
  });

  it("should build paginated response correctly", () => {
    const data = [{ id: 1 }, { id: 2 }];
    const response = buildPaginatedResponse(data, 1, 50, 100);

    expect(response.data).toEqual(data);
    expect(response.page).toBe(1);
    expect(response.limit).toBe(50);
    expect(response.total).toBe(100);
    expect(response.hasMore).toBe(true);
  });

  it("should indicate no more pages when at end", () => {
    const data = [{ id: 1 }];
    const response = buildPaginatedResponse(data, 2, 50, 100);
    expect(response.hasMore).toBe(true);

    const lastPage = buildPaginatedResponse(data, 2, 50, 75);
    expect(lastPage.hasMore).toBe(false);
  });
});

describe("Validators", () => {
  it("should validate strings", () => {
    expect(validators.isString("hello")).toBeNull();
    expect(validators.isString("")).not.toBeNull();
    expect(validators.isString(123)).not.toBeNull();
  });

  it("should validate numbers", () => {
    expect(validators.isNumber(123)).toBeNull();
    expect(validators.isNumber(NaN)).not.toBeNull();
    expect(validators.isNumber("123")).not.toBeNull();
  });

  it("should validate positive numbers", () => {
    expect(validators.isPositiveNumber(1)).toBeNull();
    expect(validators.isPositiveNumber(0)).not.toBeNull();
    expect(validators.isPositiveNumber(-1)).not.toBeNull();
  });

  it("should validate UUIDs", () => {
    const validUUID = "550e8400-e29b-41d4-a716-446655440000";
    const invalidUUID = "not-a-uuid";

    expect(validators.isUUID(validUUID)).toBeNull();
    expect(validators.isUUID(invalidUUID)).not.toBeNull();
  });
});
