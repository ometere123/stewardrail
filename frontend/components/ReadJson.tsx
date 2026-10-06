"use client";
import { useState } from "react";
import { readContract } from "@/lib/genlayer";
export function ReadJson({ address, method, args=[], label="Refresh" }: { address: string; method: string; args?: unknown[]; label?: string }) {
  const [data,setData] = useState<any>(null); const [error,setError]=useState("");
  const load=async()=>{setError(""); try{const raw=await readContract(address,method,args); setData(typeof raw === "string" ? JSON.parse(raw) : raw);}catch(e:any){setError(String(e?.message??e));}};
  return <div><button className="button secondary" onClick={load}>{label}</button>{error&&<p className="error">{error}</p>}{data!==null&&<pre className="json">{JSON.stringify(data,null,2)}</pre>}</div>;
}
