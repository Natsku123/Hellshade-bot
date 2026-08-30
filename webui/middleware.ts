import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware to add security headers for read-only API
 */
export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Security headers for read-only API
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-XSS-Protection", "1; mode=block");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set(
    "Content-Security-Policy",
    "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:",
  );
  response.headers.set("Permissions-Policy", "geolocation=(), microphone=(), camera=()");

  // Cache control for API endpoints
  if (request.nextUrl.pathname.startsWith("/api/")) {
    response.headers.set("Cache-Control", "public, max-age=60, must-revalidate");
    response.headers.set("Pragma", "no-cache");
  }

  return response;
}

// Configure which routes the middleware applies to
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
