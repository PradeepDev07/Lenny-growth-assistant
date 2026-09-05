import { NextRequest, NextResponse } from "next/server";

const FASTAPI_URL = process.env.FASTAPI_URL || "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  try {
    const { sessionId, content } = await req.json();

    if (!sessionId || !content) {
      return NextResponse.json(
        { error: { code: "INVALID_REQUEST", message: "sessionId and content are required." } },
        { status: 400 }
      );
    }

    const backendResp = await fetch(`${FASTAPI_URL}/sessions/${sessionId}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, role: "user" }),
    });

    if (!backendResp.ok || !backendResp.body) {
      return NextResponse.json(
        { error: { code: "BACKEND_STREAM_ERROR", message: "Failed to open stream to backend." } },
        { status: backendResp.status }
      );
    }

    return new Response(backendResp.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: { code: "BACKEND_UNAVAILABLE", message: error.message } },
      { status: 503 }
    );
  }
}
