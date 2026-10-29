"use client";
import { useState } from "react";
import { Activity, ArrowLeft, ArrowUpRight, Cloud, Database, Hexagon, Radio, Server, ShieldAlert, ShieldCheck, TriangleAlert } from "lucide-react";
import Link from "next/link";

const inventory = [
 {name:"edge-gateway-prod",provider:"AWS",region:"us-east-1",kind:"Network",risk:82},
 {name:"identity-control-plane",provider:"Azure",region:"eastus",kind:"Identity",risk:61},
 {name:"inference-cluster-a",provider:"GCP",region:"us-central1",kind:"Compute",risk:42},
 {name:"postgres-core",provider:"AWS",region:"us-east-1",kind:"Database",risk:26},
 {name:"onprem-auth-relay",provider:"On-prem",region:"us-dallas",kind:"Network",risk:73}
];
const alerts = [
 {title:"Suspicious cross-region authentication burst",type:"Authentication",severity:"critical",score:94},
 {title:"Network egress volume exceeds policy baseline",type:"Network",severity:"high",score:78},
 {title:"Container configuration drift detected",type:"Configuration",severity:"medium",score:46},
 {title:"Repeated unsuccessful login attempts",type:"Authentication",severity:"high",score:71}
];
const days = [{day:"Mon",v:21},{day:"Tue",v:42},{day:"Wed",v:31},{day:"Thu",v:67},{day:"Fri",v:49},{day:"Sat",v:85},{day:"Sun",v:57}];
export default function Demo() {
 const [section,setSection]=useState("Overview");
 const [filter,setFilter]=useState("all");
 const [resolved,setResolved]=useState<string[]>([]);
 const filtered=alerts.filter(x=>(filter==="all"||x.severity===filter)&&!resolved.includes(x.title));
 return <div className="app">
  <aside className="sidebar">
   <div className="brand"><span className="brandmark"><Hexagon size={21}/></span>QUORVEXIS</div>
   <div className="eyebrow" style={{padding:"0 12px"}}>INTERACTIVE DEMONSTRATION</div>
   <nav className="nav">{[{name:"Overview",icon:Activity},{name:"Threat intelligence",icon:ShieldAlert},{name:"Cloud assets",icon:Cloud}].map(({name,icon:Icon})=><button key={name} className={section===name?"selected":""} onClick={()=>setSection(name)}><Icon size={17}/>{name}</button>)}</nav>
   <div className="sidebarbottom"><span className="pill medium">SYNTHETIC DATA ONLY</span><p>No cloud integration, database, or authenticated session is used on this demonstration route.</p><Link href="/"><ArrowLeft size={13} style={{verticalAlign:"middle"}}/> Back to application</Link></div>
  </aside>
  <main className="main"><header className="topbar"><div className="crumb">Quorvexis / <strong>Interactive preview</strong></div><span className="pill medium">SIMULATED · NOT LIVE</span></header>
   <div className="content"><div className="heading"><div className="eyebrow green">SECURITY OPERATIONS / PRODUCT PREVIEW</div><h1>{section==="Overview"?"Security command center":section}</h1><p>This interactive showcase uses fictional infrastructure and client-side sample data. No real alerts are detected.</p></div>
   {section==="Overview"&&<><div className="cards">
    {[{label:"Monitored assets",value:inventory.length,icon:Server},{label:"Open incidents",value:alerts.length-resolved.length,icon:ShieldAlert},{label:"Critical alerts",value:alerts.filter(x=>x.severity==="critical"&&!resolved.includes(x.title)).length,icon:TriangleAlert},{label:"Signals · 24h",value:127,icon:Radio}].map(({label,value,icon:Icon})=><div className="card" key={label}><div className="metriclabel">{label}<Icon size={18}/></div><div className="metricvalue">{value}</div><div className="metricfoot">Demonstration metric · not a live feed</div></div>)}</div>
    <div className="grid2"><section className="card"><div className="sectionhead"><div><h2>Detection activity</h2><p style={{fontSize:12}}>Illustrative seven-day event volume</p></div><span className="pill">Sample chart</span></div><div style={{display:"flex",alignItems:"end",gap:16,height:230,padding:"10px 8px 0"}}>{days.map(d=><div key={d.day} style={{display:"flex",flex:"1",height:"100%",flexDirection:"column",alignItems:"center",justifyContent:"end",gap:9}}><div style={{background:"linear-gradient(#51dec1,#1c524e)",height:d.v+"%",width:"100%",maxWidth:62,borderRadius:"6px 6px 0 0",border:"1px solid #5be5c733"}}/><span style={{fontSize:11,color:"#8f9cb2"}}>{d.day}</span></div>)}</div></section>
    <section className="card"><h2>Risk distribution</h2><p style={{fontSize:12}}>Illustrative asset scoring</p><div style={{display:"grid",gap:20,marginTop:30}}>{[{name:"High risk",value:2,color:"#ff7c8e"},{name:"Medium risk",value:2,color:"#ffbe6f"},{name:"Low risk",value:1,color:"#53e0c4"}].map(x=><div key={x.name}><div className="flexbetween" style={{fontSize:12,marginBottom:9}}><span>{x.name}</span><span>{x.value} assets</span></div><div style={{height:9,background:"#253247",borderRadius:7}}><div style={{width:x.value/5*100+"%",height:"100%",background:x.color,borderRadius:7}}/></div></div>)}</div></section></div>
   </>}
   {(section==="Overview"||section==="Threat intelligence")&&<section className="card" style={{marginTop:16}}><div className="sectionhead"><h2>Threat intelligence queue</h2><select aria-label="Filter threat severity" className="pill" value={filter} onChange={e=>setFilter(e.target.value)}>{["all","critical","high","medium"].map(v=><option key={v} value={v}>{v==="all"?"All severities":v}</option>)}</select></div><div className="tablewrap"><table className="table"><thead><tr><th>Signal</th><th>Category</th><th>Severity</th><th>Risk score</th><th>Action</th></tr></thead><tbody>{filtered.map(x=><tr key={x.title}><td>{x.title}</td><td>{x.type}</td><td><span className={"pill "+x.severity}>{x.severity}</span></td><td>{x.score}/100</td><td><button className="button secondary" onClick={()=>setResolved([...resolved,x.title])}>Mark resolved</button></td></tr>)}</tbody></table>{!filtered.length&&<div className="empty">No matching sample events.</div>}</div></section>}
   {section==="Cloud assets"&&<section className="card"><div className="sectionhead"><h2>Sample cloud asset inventory</h2><span className="pill">{inventory.length} assets</span></div><div className="tablewrap"><table className="table"><thead><tr><th>Asset</th><th>Provider</th><th>Region</th><th>Kind</th><th>Risk</th></tr></thead><tbody>{inventory.map(x=><tr key={x.name}><td>{x.name}</td><td>{x.provider}</td><td>{x.region}</td><td>{x.kind}</td><td>{x.risk}/100</td></tr>)}</tbody></table></div></section>}
   <div className="asidecallout"><div className="eyebrow green">DEMONSTRATION BOUNDARY</div><p>Actions on this page update browser-only demo state. Refreshing restores the sample scenario. For a real workspace, run the documented Docker stack with its API and databases.</p></div>
   <p className="footer">QUORVEXIS v0.1 · SYNTHETIC INTERACTIVE DEMO · NOT A PRODUCTION SECURITY SERVICE</p>
   </div></main>
 </div>;
}
