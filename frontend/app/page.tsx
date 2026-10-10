import Link from "next/link";
import { Panel } from "@/components/Panel";

export default function Home() {
  return <>
    <section className="hero">
      <div><div className="eyebrow">Shared treasury · neutral judgment</div><h1>AI can spend. No single party gets to decide what counts.</h1><p>StewardRail gives jointly funded agents a deterministic policy rail for obvious limits and a GenLayer jury for the ambiguous remainder. Mandates are threshold-governed. Evidence is issuer-authenticated. Appeals can reverse. Money only sees a protocol-final terminal result.</p><div className="ctaRow"><Link className="button" href="/workspace">Open workspace</Link><Link className="button secondary" href="/docs">Read the trust model</Link></div></div>
      <div className="panel"><div className="kicker">SHARED AUTHORITY</div><h2>Consensus settles the semantic question.</h2><p>Deterministic policy still controls whether that result may authorize treasury value.</p></div>
    </section>
    <div className="flow"><div><b>01 Charter</b>m-of-n principals freeze a versioned mandate.</div><div><b>02 Provenance</b>Issuer wallets attest exact URI + digest + role.</div><div><b>03 Guard</b>Code rejects the obvious; validators judge the residue.</div><div><b>04 Court</b>One application appeal may affirm or reverse.</div><div><b>05 Vault</b>Exact payout only after finalized terminal delivery.</div></div>
    <div className="grid" style={{marginTop:16}}>
      <Panel eyebrow="Not just hashing" title="Issuer authenticity"><p>The mandate names authoritative issuer wallets and HTTPS origins. A digest is accepted only if the authorized wallet attested it before the spend.</p></Panel>
      <Panel eyebrow="Not cosmetic" title="Real reversal"><p>ALLOW can become REFUSE. REFUSE can become ALLOW. The appeal result becomes the effective decision delivered to custody.</p></Panel>
      <Panel eyebrow="Not accepted-only" title="Finality before money"><p>Court sends the finalized semantic result to Guard. Guard applies the economic checks, then sends a finalized authorization to Vault. The vault has no timestamp shortcut.</p></Panel>
    </div>
  </>;
}
