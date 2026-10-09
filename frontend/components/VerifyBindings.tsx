"use client";

import { useEffect, useState } from "react";
import { DEPLOYMENTS } from "@/lib/deployments";
import { readJson } from "@/lib/genlayer";

type Binding = Record<string, unknown>;

export function VerifyBindings() {
  const [rows, setRows] = useState<Record<string, Binding>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const entries = await Promise.all([
          ["Court", DEPLOYMENTS.court, "info"],
          ["Guard", DEPLOYMENTS.guard, "info"],
          ["Vault", DEPLOYMENTS.vault, "info"],
          ["BondVault", DEPLOYMENTS.bondVault, "info"],
        ].map(async ([name, address, method]) => [name, await readJson<Binding>(address, method)] as const));
        if (alive) setRows(Object.fromEntries(entries));
      } catch (cause) {
        if (alive) setError(cause instanceof Error ? cause.message : String(cause));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  if (loading) return <p className="muted">Reading live binding records…</p>;
  if (error) return <div className="errorBox"><strong>Live binding read failed</strong><p>{error}</p><p className="muted">The configured addresses are not treated as verified until these reads succeed.</p></div>;
  return <div className="bindingGrid">
    {Object.entries(rows).map(([name, data]) => <div className="bindingCard" key={name}>
      <div className="row between"><strong>{name}</strong><span className="pill good">READ OK</span></div>
      <dl>{Object.entries(data).filter(([key]) => ["charter", "registry", "guard", "court", "vault", "bond_vault", "agent"].includes(key)).map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd className="mono">{String(value)}</dd></div>)}</dl>
      <details><summary>View raw</summary><pre className="json">{JSON.stringify(data, null, 2)}</pre></details>
    </div>)}
  </div>;
}
