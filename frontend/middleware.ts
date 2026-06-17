import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

  // Middleware runs on the server — can't read localStorage.
  // Auth guard is enforced client-side in the dashboard layout.
  // This middleware only handles /login redirect when a session cookie exists in future.
  if (isPublic) return NextResponse.next();
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
