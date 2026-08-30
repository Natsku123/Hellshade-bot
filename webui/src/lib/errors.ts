/**
 * Centralized error handling and logging utilities
 */

export type ApiError = {
  error: string;
  code?: string;
  details?: Record<string, unknown>;
};

export class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code?: string,
    public details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "AppError";
  }
}

export function logError(error: unknown, context?: string): void {
  const prefix = context ? `[${context}]` : "";
  if (error instanceof Error) {
    console.error(`${prefix} ${error.name}: ${error.message}`);
  } else {
    console.error(`${prefix} Unknown error:`, error);
  }
}

export function toApiError(error: unknown, defaultMessage = "Internal server error"): ApiError {
  if (error instanceof AppError) {
    return {
      error: error.message,
      code: error.code,
      details: error.details,
    };
  }

  if (error instanceof Error) {
    return {
      error: error.message || defaultMessage,
    };
  }

  return {
    error: defaultMessage,
  };
}
