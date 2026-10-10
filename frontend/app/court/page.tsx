"use client";
import { useEffect, useState } from "react";
import { Panel } from "@/components/Panel";
import { DEPLOYMENTS } from "@/lib/deployments";
import { WriteAction } from "@/components/WriteAction";
import { ReadJson } from "@/components/ReadJson";
import { formatGen, parseGen } from "@/lib/gen";
import { readContract } from "@/lib/genlayer";

type ChallengeRecord = {
  id?: number;
  spend_id?: number;
  state?: string;
  bond?: number | string;
  deadline?: number | string;
  adjudication_deadline?: number | string;
  registration_deadline?: number | string;
  registered?: boolean;
  court_status?: string;
  settlement?: string;
};

function ChallengeStatus({ challengeId, onRecord }: { challengeId: number; onRecord: (record: ChallengeRecord | null) => void }) {
  const [record, setRecord] = useState<ChallengeRecord | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const refresh = async () => {
    setLoading(true); setError("");
    try {
      const [bondRaw, courtRaw] = await Promise.all([
        readContract(DEPLOYMENTS.bondVault, "challenge", [challengeId]),
        readContract(DEPLOYMENTS.court, "challenge", [DEPLOYMENTS.guard, challengeId]).catch(() => null),
      ]);
      const next = typeof bondRaw === "string" ? JSON.parse(bondRaw) : bondRaw;
      const court = typeof courtRaw === "string" ? JSON.parse(courtRaw) : courtRaw;
      if (court) Object.assign(next, { court_status: court.status, adjudication_deadline: court.adjudication_deadline });
      setRecord(next); onRecord(next);
    } catch (e: any) { setRecord(null); onRecord(null); setError(String(e?.message ?? e)); }
    finally { setLoading(false); }
  };
  useEffect(() => { setRecord(null); onRecord(null); }, [challengeId, onRecord]);
  const epoch = (value: unknown) => Number(value || 0);
  const status = String(record?.state || "unknown").toUpperCase();
  const now = Math.floor(Date.now() / 1000);
  const deadline = epoch(record?.deadline);
  const adjudicationDeadline = epoch(record?.adjudication_deadline);
  const registrationDeadline = epoch(record?.registration_deadline);
  return <div className="challengeStatus">
    <div className="between row"><div><strong>Challenge {challengeId}</strong><span className={`pill ${status === "OPEN" ? "warn" : status === "SETTLED" ? "good" : ""}`}>{status}</span></div><button className="button secondary" onClick={refresh} disabled={loading}>{loading ? "Reading…" : "Refresh challenge status"}</button></div>
    {error && <p className="error">{error}</p>}
    {record && <div className="challengeFacts">
      <div><small>Spend ID</small><strong>{record.spend_id ?? "—"}</strong></div>
      <div><small>Registration</small><strong>{record.registered ? "Acknowledged" : registrationDeadline && now >= registrationDeadline ? "Expired" : "Pending"}</strong></div>
      <div><small>Response deadline</small><strong>{deadline ? new Date(deadline * 1000).toLocaleString() : "—"}</strong></div>
      <div><small>Adjudication deadline</small><strong>{adjudicationDeadline ? new Date(adjudicationDeadline * 1000).toLocaleString() : "Pending Court record"}</strong></div>
      <div><small>Bond</small><strong>{record.bond !== undefined ? `${formatGen(BigInt(String(record.bond)))} GEN` : "—"}</strong></div>
    </div>}
    {!record && !error && <p className="muted">Read the challenge ID to see its state, registration and response deadlines before acting.</p>}
    {record?.settlement && <p className="muted">Settlement: {record.settlement}</p>}
    {record && <details className="rawDetails"><summary>View raw challenge record</summary><pre className="json">{JSON.stringify(record, null, 2)}</pre></details>}
  </div>;
}

export default function Court(){
  const [id,setId]=useState("0");
  const [challengeId,setChallengeId]=useState("0");
  const [statement,setStatement]=useState("Reconsider the frozen record; the primary decision misread the authenticated evidence.");
  const [appealEvidence,setAppealEvidence]=useState("[]");
  const [challengeValue,setChallengeValue]=useState("1");
  const [bondValue,setBondValue]=useState("0.01");
  const [cause,setCause]=useState("The terminal authorization is not supported by the authenticated record.");
  const [challengeEvidence,setChallengeEvidence]=useState("[]");
  const [challengeRecord,setChallengeRecord]=useState<ChallengeRecord | null>(null);
  let challengeUnits=0n; let bondUnits=0n;
  try { challengeUnits=parseGen(challengeValue); } catch { /* WriteAction will remain safely zero until corrected. */ }
  try { bondUnits=parseGen(bondValue); } catch { /* WriteAction will remain safely zero until corrected. */ }
  const parsedChallengeId = Number.parseInt(challengeId, 10);
  const validChallengeId = Number.isInteger(parsedChallengeId) && parsedChallengeId >= 0;
  const now = Math.floor(Date.now() / 1000);
  const challengeState = String(challengeRecord?.state || "").toLowerCase();
  const responseDeadline = Number(challengeRecord?.deadline || 0);
  const adjudicationDeadline = Number(challengeRecord?.adjudication_deadline || 0);
  const registrationReady = !challengeRecord || (challengeState === "open" && !challengeRecord.registered);
  const responseReady = !challengeRecord || (challengeState === "open" && Boolean(challengeRecord.registered) && now >= responseDeadline);
  const adjudicationReady = !challengeRecord || (challengeState === "open" && Boolean(challengeRecord.registered) && adjudicationDeadline > 0 && now >= adjudicationDeadline);
  const reconcileReady = !challengeRecord || String(challengeRecord.court_status || "").toLowerCase() === "terminal";
  const challengeArg = validChallengeId ? parsedChallengeId : 0;
  const unavailable = (message: string, condition: boolean) => condition ? message : undefined;
  return <><div className="routeTag">/court</div><h1 className="sectionTitle">Appeal, not override</h1><p className="sectionIntro">No principal has an allow/refuse override. An eligible principal, agent, or recipient may ask a fresh validator panel to re-decide the frozen record.</p><div className="grid"><Panel title="Case" className="wide"><div className="field"><label htmlFor="court-spend-id">Spend ID</label><input id="court-spend-id" value={id} onChange={e=>setId(e.target.value)}/></div><div className="field"><label htmlFor="appeal-statement">Appeal statement (argument, not evidence)</label><textarea id="appeal-statement" value={statement} onChange={e=>setStatement(e.target.value)}/></div><div className="field"><label htmlFor="appeal-evidence">Additional issuer-attested appeal evidence JSON</label><textarea id="appeal-evidence" value={appealEvidence} onChange={e=>setAppealEvidence(e.target.value)} placeholder='[{"issuer":"0x…","role":"auditor","uri":"https://…","digest":"…"}]'/></div><div className="row"><ReadJson address={DEPLOYMENTS.court} method="case" args={[DEPLOYMENTS.guard,Number(id)]}/><WriteAction address={DEPLOYMENTS.court} method="appeal" args={[DEPLOYMENTS.guard,Number(id),DEPLOYMENTS.vault,statement,appealEvidence]} action="Appeal spend" label="Appeal"/></div></Panel><Panel title="Unappealed close"><p>After the application window expires, anyone may close the case. The terminal message still waits for the close transaction to finalize.</p><WriteAction address={DEPLOYMENTS.court} method="close_unappealed" args={[DEPLOYMENTS.guard,Number(id),DEPLOYMENTS.vault]} action="Close unappealed case" label="Close after deadline"/></Panel><Panel title="Bonded challenge" className="wide"><p className="muted">A bonded challenge is separate from an application appeal. It requires frozen-mandate evidence and an exact quoted bond.</p><div className="formGrid"><div className="field"><label htmlFor="challenge-value">Challenged amount (GEN)</label><input id="challenge-value" inputMode="decimal" value={challengeValue} onChange={e=>setChallengeValue(e.target.value)}/></div><div className="field"><label htmlFor="challenge-bond">Quoted bond (GEN)</label><input id="challenge-bond" inputMode="decimal" value={bondValue} onChange={e=>setBondValue(e.target.value)}/></div></div><div className="field"><label htmlFor="challenge-cause">Challenge cause</label><textarea id="challenge-cause" value={cause} onChange={e=>setCause(e.target.value)}/></div><div className="field"><label htmlFor="challenge-evidence">Authenticated challenge evidence JSON</label><textarea id="challenge-evidence" value={challengeEvidence} onChange={e=>setChallengeEvidence(e.target.value)} placeholder='[{"issuer":"0x…","role":"delivery","uri":"https://…","digest":"…"}]'/></div><div className="row"><ReadJson address={DEPLOYMENTS.bondVault} method="quote_bond" args={[challengeUnits,Number(id)]} label="Read frozen bond quote"/><WriteAction address={DEPLOYMENTS.bondVault} method="open_challenge" args={[Number(id),challengeUnits,cause,challengeEvidence]} value={bondUnits} action="Open bonded challenge" label="Open challenge"/></div></Panel><Panel title="Challenge progression" className="full challengeProgression"><div className="challengeHeader"><div><p className="muted">Challenge IDs are issued by BondVault and are separate from Spend IDs. Use the spend ID above for the case, bond quote and challenge opening; use this ID for progression and challenge readbacks.</p><div className="field"><label htmlFor="challenge-id">Challenge ID</label><input id="challenge-id" inputMode="numeric" value={challengeId} onChange={e=>setChallengeId(e.target.value)} /></div></div><ChallengeStatus challengeId={challengeArg} onRecord={setChallengeRecord}/></div><div className="actionGrid"><div className="actionCard"><h3>Reconcile challenge registration</h3><p className="muted">Forward the BondVault registration to Court before the response window can begin.</p><WriteAction address={DEPLOYMENTS.bondVault} method="reconcile_open_challenge" args={[challengeArg]} disabled={!validChallengeId || !registrationReady} disabledReason={!validChallengeId ? "Enter a non-negative Challenge ID." : unavailable("Registration is already acknowledged or the challenge is no longer open.", !registrationReady)} action="Reconcile challenge registration" label="Reconcile registration"/></div><div className="actionCard"><h3>Resolve challenge</h3><p className="muted">After the response deadline, ask Court validators to decide the challenge.</p><WriteAction address={DEPLOYMENTS.court} method="resolve_challenge" args={[DEPLOYMENTS.guard,challengeArg,DEPLOYMENTS.bondVault]} disabled={!validChallengeId || !responseReady} disabledReason={!validChallengeId ? "Enter a non-negative Challenge ID." : unavailable("The response window is still open, registration is pending, or the case is terminal.", !responseReady)} action="Resolve challenge" label="Resolve after deadline"/></div><div className="actionCard"><h3>Expire challenge</h3><p className="muted">If adjudication does not complete by its frozen deadline, close the case deterministically.</p><WriteAction address={DEPLOYMENTS.court} method="expire_challenge" args={[DEPLOYMENTS.guard,challengeArg,DEPLOYMENTS.bondVault]} disabled={!validChallengeId || !responseReady} disabledReason={!validChallengeId ? "Enter a non-negative Challenge ID." : unavailable("The challenge is not open or its response deadline has not passed.", !responseReady)} action="Expire challenge" label="Expire after timeout"/></div><div className="actionCard"><h3>Reconcile challenge result</h3><p className="muted">Re-emit the finalized Court result to Guard when downstream delivery needs recovery.</p><WriteAction address={DEPLOYMENTS.court} method="reconcile_challenge" args={[DEPLOYMENTS.guard,challengeArg,DEPLOYMENTS.bondVault]} disabled={!validChallengeId || !reconcileReady} disabledReason={!validChallengeId ? "Enter a non-negative Challenge ID." : unavailable("Only a terminal Court challenge can be reconciled.", !reconcileReady)} action="Reconcile challenge result" label="Reconcile result"/></div></div></Panel></div></>;
}
