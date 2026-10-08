"use client";
import { useState } from "react";
import { useWallet } from "@/lib/wallet";

export function WalletButton() {
  const w = useWallet();
  const [error, setError] = useState("");
  if (!w.connected) return <button className="button" onClick={() => w.connect().catch(e => setError(String(e.message ?? e)))}>{error || "Connect wallet"}</button>;
  if (!w.correctNetwork) return <button className="button danger" onClick={() => w.switchNetwork().catch(e => setError(String(e.message ?? e)))}>{error || `Switch to 61999`}</button>;
  return <div className="walletCluster"><span className="walletPill">{w.address.slice(0,6)}…{w.address.slice(-4)} · Studionet</span><button className="button secondary" onClick={w.disconnect}>Disconnect</button></div>;
}
