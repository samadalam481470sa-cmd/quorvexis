import { NextRequest, NextResponse } from "next/server";
const API = process.env.API_INTERNAL_URL || "http://localhost:8000";
const secure = process.env.NODE_ENV === "production";
const cookie = "qvx_session";
export async function POST(req: NextRequest) {
  const origin = req.headers.get("origin");
  if (origin !== req.nextUrl.origin) return NextResponse.json({detail:"Origin not allowed"}, {status:403});
  const payload = await req.text();
  if (payload.length > 8192) return NextResponse.json({detail:"Request too large"}, {status:413});
  const mode = req.nextUrl.searchParams.get("mode") === "register" ? "register" : "login";
  try {
    const upstream = await fetch(API + "/auth/" + mode, { method:"POST", body:payload,
      headers:{"content-type":"application/json"}, cache:"no-store", signal:AbortSignal.timeout(10000) });
    const data = await upstream.json();
    if (!upstream.ok) return NextResponse.json({detail:data.detail || "Authentication failed"}, {status:upstream.status});
    const result = NextResponse.json({user:data.user});
    result.cookies.set(cookie, data.access_token, {httpOnly:true,secure,sameSite:"strict",path:"/",maxAge:900});
    return result;
  } catch { return NextResponse.json({detail:"Service unavailable"},{status:503}); }
}
export async function DELETE(req: NextRequest) {
  if (req.headers.get("origin") !== req.nextUrl.origin) return NextResponse.json({detail:"Origin not allowed"}, {status:403});
  const out=NextResponse.json({ok:true});
  out.cookies.delete(cookie);
  return out;
}
