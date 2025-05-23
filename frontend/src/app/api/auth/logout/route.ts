import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function POST() {
  // Clear the authentication cookie
  cookies().delete("auth-token");
  
  return NextResponse.json({ success: true });
}