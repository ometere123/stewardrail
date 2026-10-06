"use client";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { TxRecord } from "./types";

const KEY = "stewardrail.tx.v1";
const Ctx = createContext<{ tx: TxRecord; setTx: (tx: TxRecord) => void } | null>(null);
export function TxProvider({ children }: { children: React.ReactNode }) {
  const [tx, setTxState] = useState<TxRecord>({ phase: "idle" });
  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setTxState(JSON.parse(raw));
    } catch { /* local persistence is non-authoritative */ }
  }, []);
  const setTx = (next: TxRecord) => {
    setTxState(next);
    try {
      if (next.phase === "idle") localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, JSON.stringify(next));
    } catch { /* UI persistence must never block a transaction */ }
  };
  const value = useMemo(() => ({ tx, setTx }), [tx]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
export function useTx() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useTx must be inside TxProvider");
  return value;
}
