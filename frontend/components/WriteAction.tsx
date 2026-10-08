"use client";
import { useState } from "react";
import { useWallet } from "@/lib/wallet";
import { useTx } from "@/lib/tx";
import { writeContract } from "@/lib/genlayer";
import { NETWORK } from "@/lib/deployments";
import { formatGen } from "@/lib/gen";

export function WriteAction({ address, method, action, args, value=0n, label }: { address: string; method: string; action: string; args: unknown[]; value?: bigint; label: string }) {
  const wallet = useWallet();
  const { setTx } = useTx();
  const [error, setError] = useState("");
  const go = async () => {
    setError("");
    if (!wallet.connected) return setError("Connect an injected wallet first.");
    if (!wallet.correctNetwork) return setError("Wrong network: switch to Studionet 61999 first.");
    if (!address) return setError("Deployment address is not configured yet.");
    try {
      await writeContract({ address, functionName: method, args, value, account: wallet.address, action, onProgress: setTx });
    } catch (e: any) { setError(String(e?.message ?? e)); }
  };
  return <div className="writeAction">
    <div className="txPreview">
      <small>ACTION</small><b>{action}</b>
      <small>CONTRACT</small><code>{address || "not deployed"}</code>
      <small>NETWORK / VALUE</small><code>{NETWORK.name} · {NETWORK.chainId} · {formatGen(value)} GEN</code>
    </div>
    <button className="button" onClick={go}>{label}</button>{error && <p className="error">{error}</p>}
  </div>;
}
