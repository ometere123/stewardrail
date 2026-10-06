"use client";
import { useTx } from "@/lib/tx";
import { NETWORK } from "@/lib/deployments";
import { resumeFinalization } from "@/lib/genlayer";
import { useState } from "react";

export function TxDrawer() {
  const { tx, setTx } = useTx();
  const [resumeError,setResumeError]=useState("");
  if (tx.phase === "idle") return null;
  return <aside className="txDrawer">
    <div className="row between"><strong>Transaction</strong><button className="textButton" onClick={() => setTx({phase:"idle"})}>close</button></div>
    <div className={`status ${tx.phase}`}>{tx.phase}</div>
    <p>{tx.action}</p>
    {tx.hash && <a target="_blank" rel="noreferrer" href={`${NETWORK.explorer}/tx/${tx.hash}`}>{tx.hash.slice(0,18)}…</a>}
    {tx.status && <small>{tx.status} · {tx.execution}</small>}
    {tx.hash && (tx.phase === "submitted" || tx.phase === "decided") && <button className="button secondary" onClick={() => resumeFinalization(tx.hash!,tx,setTx).catch(e=>setResumeError(String(e?.message??e)))}>Resume finalization</button>}
    {resumeError && <p className="error">{resumeError}</p>}
    {tx.error && <p className="error">{tx.error}</p>}
  </aside>;
}
