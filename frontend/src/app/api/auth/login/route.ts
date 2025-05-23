import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import crypto from "crypto";

// Set your password here or use environment variable
const SITE_PASSWORD = process.env.SITE_PASSWORD || "5g-analyzer-2024";

// Generate a secret for signing cookies
const COOKIE_SECRET = process.env.COOKIE_SECRET || "your-secret-key-change-this-in-production";

export async function POST(request: NextRequest) {
  try {
    const { password } = await request.json();

    if (password === SITE_PASSWORD) {
      // Create a signed token
      const token = crypto
        .createHmac("sha256", COOKIE_SECRET)
        .update(`authenticated-${Date.now()}`)
        .digest("hex");

      // Set authentication cookie
      cookies().set("auth-token", token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "strict",
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: "/",
      });

      return NextResponse.json({ success: true });
    } else {
      return NextResponse.json(
        { error: "Invalid password" },
        { status: 401 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      { error: "Invalid request" },
      { status: 400 }
    );
  }
}