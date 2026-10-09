"use client";

import { useState } from "react";
import { DEPLOYMENTS } from "@/lib/deployments";
import { Panel } from "@/components/Panel";
import { WriteAction } from "@/components/WriteAction";
import { ReadJson } from "@/components/ReadJson";
import { parseGen } from "@/lib/gen";

export default function Vault() {
  const [fund, setFund] = useState("1");
  const [id, setId] = useState("0");
  const [standing, setStanding] = useState("1");
  const [withdraw, setWithdraw] = useState("0.1");
  const [to, setTo] = useState("");
  let units = 0n; let standingUnits = 0n; let withdrawUnits = 0n; let fundError = "";
  try { units = parseGen(fund); } catch (e) { fundError = String((e as Error).message); }
  try { standingUnits = parseGen(standing); } catch { /* validation is surfaced by the input context */ }
  try { withdrawUnits = parseGen(withdraw); } catch { /* validation is surfaced by the input context */ }
  return <>
    <div className="routeTag">/vault</div>
    <h1 className="sectionTitle">Custody rail</h1>
    <p className="sectionIntro">The agent cannot withdraw. The vault cannot adjudicate. It pays an exact terminal ALLOW once.</p>
    <div className="grid">
      <Panel title="Treasury" className="wide">
        <ReadJson address={DEPLOYMENTS.vault} method="status" />
        <div className="divider" />
        <div className="formGrid">
          <div className="field"><label htmlFor="fund-amount">Fund amount (GEN)</label><div className="amountField"><input id="fund-amount" inputMode="decimal" value={fund} onChange={e => setFund(e.target.value)} /><span>GEN</span></div>{fundError && <p className="error">{fundError}</p>}</div>
          <div className="field"><label htmlFor="spend-id">Spend ID</label><input id="spend-id" value={id} onChange={e => setId(e.target.value)} /></div>
        </div>
        <div className="ctaRow"><WriteAction address={DEPLOYMENTS.vault} method="fund" args={[]} value={units} action="Fund shared treasury" label="Fund vault" /><WriteAction address={DEPLOYMENTS.vault} method="pay" args={[Number(id)]} action="Settle terminal spend" label="Pay terminal allow" /></div>
      </Panel>
      <Panel title="Payment state"><ReadJson address={DEPLOYMENTS.vault} method="payment" args={[Number(id)]} /></Panel>
      <Panel title="Standing collateral" className="wide">
        <p className="muted">Standing collateral belongs to the configured agent and remains locked behind challengeable obligations.</p>
        <ReadJson address={DEPLOYMENTS.bondVault} method="status" />
        <div className="formGrid">
          <div className="field"><label htmlFor="standing-amount">Deposit standing (GEN)</label><div className="amountField"><input id="standing-amount" inputMode="decimal" value={standing} onChange={e => setStanding(e.target.value)} /><span>GEN</span></div></div>
          <div className="field"><label htmlFor="withdraw-amount">Withdraw available (GEN)</label><div className="amountField"><input id="withdraw-amount" inputMode="decimal" value={withdraw} onChange={e => setWithdraw(e.target.value)} /><span>GEN</span></div></div>
        </div>
        <div className="field"><label htmlFor="standing-recipient">Withdrawal recipient</label><input id="standing-recipient" value={to} onChange={e => setTo(e.target.value)} placeholder="Agent address" /></div>
        <div className="ctaRow"><WriteAction address={DEPLOYMENTS.bondVault} method="deposit_standing" args={[]} value={standingUnits} action="Deposit standing collateral" label="Deposit standing" /><WriteAction address={DEPLOYMENTS.bondVault} method="withdraw_standing" args={[to, withdrawUnits]} action="Withdraw standing collateral" label="Withdraw available" /><WriteAction address={DEPLOYMENTS.bondVault} method="release_expired_exposure" args={[Number(id)]} action="Release expired standing lock" label="Release expired lock" /></div>
      </Panel>
    </div>
  </>;
}
