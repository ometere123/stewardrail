"use client";
import { useState } from "react";
import { Panel } from "@/components/Panel";
import { DEPLOYMENTS } from "@/lib/deployments";
import { WriteAction } from "@/components/WriteAction";
import { ReadJson } from "@/components/ReadJson";
export default function Court(){
  const [id,setId]=useState("0");
  const [statement,setStatement]=useState("Reconsider the frozen record; the primary decision misread the authenticated evidence.");
  const [appealEvidence,setAppealEvidence]=useState("[]");
  return <><div className="routeTag">/court</div><h1 className="sectionTitle">Appeal, not override</h1><p className="sectionIntro">No principal has an allow/refuse override. An eligible principal, agent, or recipient may ask a fresh validator panel to re-decide the frozen record.</p><div className="grid"><Panel title="Case" className="wide"><div className="field"><label>Spend ID</label><input value={id} onChange={e=>setId(e.target.value)}/></div><div className="field"><label>Appeal statement</label><textarea value={statement} onChange={e=>setStatement(e.target.value)}/></div><div className="field"><label>Additional issuer-attested appeal evidence JSON</label><textarea value={appealEvidence} onChange={e=>setAppealEvidence(e.target.value)} placeholder='[{"issuer":"0x…","role":"auditor","uri":"https://…","digest":"…"}]'/></div><div className="row"><ReadJson address={DEPLOYMENTS.court} method="case" args={[DEPLOYMENTS.guard,Number(id)]}/><WriteAction address={DEPLOYMENTS.court} method="appeal" args={[DEPLOYMENTS.guard,Number(id),DEPLOYMENTS.vault,statement,appealEvidence]} action="Appeal spend" label="Appeal"/></div></Panel><Panel title="Unappealed close"><p>After the application window expires, anyone may close the case. The terminal message still waits for the close transaction to finalize.</p><WriteAction address={DEPLOYMENTS.court} method="close_unappealed" args={[DEPLOYMENTS.guard,Number(id),DEPLOYMENTS.vault]} action="Close unappealed case" label="Close after deadline"/></Panel></div></>;
}
