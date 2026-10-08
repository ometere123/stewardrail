import Link from "next/link";
import { DEPLOYMENTS, deployed } from "@/lib/deployments";
import { Panel, Stat } from "@/components/Panel";
import { ReadJson } from "@/components/ReadJson";

export default function Workspace(){return <>
  <div className="routeTag">/workspace</div><h1 className="sectionTitle">Shared treasury control room</h1><p className="sectionIntro">Inspect the frozen charter, agent docket, court and custody rail. Read-only verification stays separate from signing actions.</p>
  {!deployed&&<div className="notice">Deployment configuration is unavailable. Add the required public environment variables before using the workspace.</div>}
  <div className="grid" style={{marginTop:16}}>
    <Panel title="Deployment" className="wide"><div className="stats"><Stat label="NETWORK" value="61999" note="stable Studionet"/><Stat label="CONTRACTS" value="5" note="exact readable sources"/><Stat label="STATUS" value={deployed?"LIVE":"PRE-DEPLOY"}/></div><div className="divider"/><p className="mono">Guard: {DEPLOYMENTS.guard||"not deployed"}</p><p className="mono">Vault: {DEPLOYMENTS.vault||"not deployed"}</p></Panel>
    <Panel title="Actions"><div className="stack"><Link className="button" href="/charters/new">Create charter</Link><Link className="button secondary" href="/spends/new">Request spend</Link><Link className="button secondary" href="/evidence">Attest evidence</Link></div></Panel>
    <Panel title="Charter"><ReadJson address={DEPLOYMENTS.charter} method="current" /></Panel>
    <Panel title="Docket"><ReadJson address={DEPLOYMENTS.guard} method="docket" /></Panel>
    <Panel title="Vault"><ReadJson address={DEPLOYMENTS.vault} method="status" /></Panel>
  </div>
</>}
