import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  // Check if the user is trying to access the login page
  if (request.nextUrl.pathname === "/login") {
    // If they have a valid auth token, redirect to home
    const authToken = request.cookies.get("auth-token");
    if (authToken) {
      return NextResponse.redirect(new URL("/", request.url));
    }
    // Otherwise, let them access the login page
    return NextResponse.next();
  }

  // For all other pages, check authentication
  const authToken = request.cookies.get("auth-token");
  
  // If no auth token, redirect to login
  if (!authToken) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // If authenticated, allow access
  return NextResponse.next();
}

// Configure which routes to protect
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api/auth (authentication endpoints)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!api/auth|_next/static|_next/image|favicon.ico|public).*)",
  ],
};