import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const FASTAPI_URL = (process.env.FASTAPI_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

export async function GET() {
  try {
    const res = await fetch(`${FASTAPI_URL}/sessions`, { cache: "no-store" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: any) {
    return NextResponse.json(
      { error: { code: "BACKEND_UNAVAILABLE", message: error.message } },
      { status: 503 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const res = await fetch(`${FASTAPI_URL}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: any) {
    return NextResponse.json(
      { error: { code: "BACKEND_UNAVAILABLE", message: error.message } },
      { status: 503 }
    );
  }
}
