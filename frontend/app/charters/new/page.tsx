"use client";
import { useState } from "react";
import { Panel } from "@/components/Panel";
import { NETWORK } from "@/lib/deployments";

export default function NewCharter(){
  const [principals,setPrincipals]=useState('["0x...","0x...","0x..."]'); const [threshold,setThreshold]=useState("2"); const [agent,setAgent]=useState("0x");
  return <><div className="routeTag">/charters/new</div><h1 className="sectionTitle">Compose a shared charter</h1><p className="sectionIntro">This route deliberately prepares deployment inputs; it does not hide contract deployment behind an application backend. Deploy with the repository-local CLI on chain {NETWORK.chainId}.</p><div className="grid"><Panel title="Charter inputs" className="wide"><div className="stack"><div className="field"><label>Principal addresses JSON</label><textarea value={principals} onChange={e=>setPrincipals(e.target.value)}/></div><div className="formGrid"><div className="field"><label>Threshold</label><input value={threshold} onChange={e=>setThreshold(e.target.value)}/></div><div className="field"><label>Agent</label><input value={agent} onChange={e=>setAgent(e.target.value)}/></div></div><div className="notice">Initial mandate also requires threshold approval on-chain. Deployment alone cannot activate it.</div><pre className="json">{`npx --no-install genlayer deploy --contract contracts/steward_charter.py --args '${principals}' ${threshold} ${agent} '<mandate-json>'`}</pre></div></Panel><Panel title="Why no one-click deploy?"><p>Deployment must use the exact checked-in Python source and the repository-pinned CLI. The UI avoids bundling a second contract representation.</p></Panel></div></>;
}
