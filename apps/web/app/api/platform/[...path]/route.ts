import { NextRequest, NextResponse } from "next/server";
const API = process.env.API_INTERNAL_URL || "http://localhost:8000";
const allowed = new Set(["me","overview","assets","incidents","signals","demo/seed"]);
type Context={params:Promise<{path:string[]}>};
async function proxy(req:NextRequest,ctx:Context) {
  const path=(await ctx.params).path;
  const route=path.join("/");
  const valid=allowed.has(route) || (path.length===2 && path[0]==="incidents" && /^[0-9a-f-]{36}$/i.test(path[1]));
  if (!valid) return NextResponse.json({detail:"Not found"}, {status:404});
  if (req.method!=="GET" && req.headers.get("origin")!==req.nextUrl.origin)
    return NextResponse.json({detail:"Origin not allowed"}, {status:403});
  const token=req.cookies.get("qvx_session")?.value;
  if (!token) return NextResponse.json({detail:"Authentication required"}, {status:401});
  const body=req.method==="GET"?undefined:await req.text();
  if (body && body.length>1048576) return NextResponse.json({detail:"Request too large"},{status:413});
  try {
    const upstream=await fetch(API+"/"+route,{method:req.method,body,
      headers:{"authorization":"Bearer "+token,...(body?{"content-type":"application/json"}:{})},
      cache:"no-store",signal:AbortSignal.timeout(12000)});
    const data=await upstream.json();
    const out=NextResponse.json(data,{status:upstream.status});
    out.headers.set("cache-control","no-store");
    if(upstream.status===401)out.cookies.delete("qvx_session");
    return out;
  }catch{return NextResponse.json({detail:"Service unavailable"},{status:503});}
}
export const GET=proxy;
export const POST=proxy;
export const PATCH=proxy;
