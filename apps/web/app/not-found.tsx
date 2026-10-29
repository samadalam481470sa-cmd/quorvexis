import Link from "next/link";
export default function NotFound(){return <main style={{minHeight:"100vh",display:"grid",placeItems:"center",padding:24}}><div style={{textAlign:"center"}}><h1>Page not found</h1><p>This page isn't part of the Quorvexis command center.</p><Link className="button" href="/demo">Open interactive demo</Link></div></main>}
