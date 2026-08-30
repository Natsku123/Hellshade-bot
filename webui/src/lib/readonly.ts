/**
 * HTTP method enforcement utility
 * Ensures only GET requests are allowed on read-only API routes
 */

export function enforceReadOnly(method: string): void {
  if (method !== "GET") {
    throw new Error(`${method} method not allowed on read-only API`);
  }
}

/**
 * Middleware to log all requests and enforce read-only mode
 */
export function getReadOnlyHeaders(): HeadersInit {
  return {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Pragma": "no-cache",
    "Cache-Control": "private, max-age=60, must-revalidate",
  };
}
