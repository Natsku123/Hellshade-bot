import { describe, it, expect, vi } from "vitest";
import { AppError, toApiError, logError } from "@/lib/errors";

describe("Error Handling", () => {
  it("should create AppError with all properties", () => {
    const error = new AppError("Test error", 400, "TEST_CODE", { field: "value" });

    expect(error.message).toBe("Test error");
    expect(error.statusCode).toBe(400);
    expect(error.code).toBe("TEST_CODE");
    expect(error.details).toEqual({ field: "value" });
  });

  it("should convert AppError to API error", () => {
    const error = new AppError("Validation failed", 400, "VALIDATION_ERROR", {
      email: "Invalid email",
    });
    const apiError = toApiError(error);

    expect(apiError.error).toBe("Validation failed");
    expect(apiError.code).toBe("VALIDATION_ERROR");
    expect(apiError.details).toEqual({ email: "Invalid email" });
  });

  it("should convert regular Error to API error", () => {
    const error = new Error("Something went wrong");
    const apiError = toApiError(error);

    expect(apiError.error).toBe("Something went wrong");
    expect(apiError.code).toBeUndefined();
  });

  it("should handle non-Error values", () => {
    const apiError = toApiError("unknown error");
    expect(apiError.error).toBe("Internal server error");

    const apiError2 = toApiError(null, "Custom default");
    expect(apiError2.error).toBe("Custom default");
  });

  it("should log errors", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    const error = new Error("Test error");
    logError(error, "TEST_CONTEXT");

    expect(consoleSpy).toHaveBeenCalledWith("[TEST_CONTEXT] Error: Test error");

    consoleSpy.mockRestore();
  });

  it("should log non-Error values", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    logError("string error");

    expect(consoleSpy).toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});
