import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const FASTAPI_URL = (process.env.FASTAPI_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const res = await fetch(`${FASTAPI_URL}/sessions/${params.id}`, { cache: "no-store" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: any) {
    return NextResponse.json(
      { error: { code: "BACKEND_UNAVAILABLE", message: error.message } },
      { status: 503 }
    );
  }
}

export async function DELETE(req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const res = await fetch(`${FASTAPI_URL}/sessions/${params.id}`, { method: "DELETE" });
    if (res.status === 204) {
      return new Response(null, { status: 204 });
    }
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: any) {
    return NextResponse.json(
      { error: { code: "BACKEND_UNAVAILABLE", message: error.message } },
      { status: 503 }
    );
  }
}
