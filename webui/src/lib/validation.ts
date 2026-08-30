/**
 * Request validation utilities
 */

import { AppError } from "@/lib/errors";

export type ValidationRule<T> = {
  [K in keyof T]?: (value: unknown) => string | null;
};

export function validateRequest<T extends Record<string, unknown>>(
  data: unknown,
  rules: ValidationRule<T>,
): T {
  if (!data || typeof data !== "object") {
    throw new AppError("Invalid request body", 400, "INVALID_REQUEST");
  }

  const result: Record<string, unknown> = {};
  const errors: Record<string, string> = {};

  for (const [key, rule] of Object.entries(rules)) {
    const value = (data as Record<string, unknown>)[key];
    if (rule) {
      const error = rule(value);
      if (error) {
        errors[key] = error;
      } else {
        result[key] = value;
      }
    }
  }

  if (Object.keys(errors).length > 0) {
    throw new AppError("Validation failed", 400, "VALIDATION_ERROR", errors);
  }

  return result as T;
}

export const validators = {
  isString: (value: unknown): string | null =>
    typeof value === "string" && value.length > 0 ? null : "Must be a non-empty string",

  isNumber: (value: unknown): string | null =>
    typeof value === "number" && !isNaN(value) ? null : "Must be a valid number",

  isUUID: (value: unknown): string | null =>
    typeof value === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value)
      ? null
      : "Must be a valid UUID",

  isPositiveNumber: (value: unknown): string | null =>
    typeof value === "number" && value > 0 ? null : "Must be a positive number",
};
