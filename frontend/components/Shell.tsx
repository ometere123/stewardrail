"use client";
import Link from "next/link";
import { useState } from "react";
import { WalletButton } from "./WalletButton";
import { TxDrawer } from "./TxDrawer";

const nav = [
  ["/workspace","Workspace"],["/spends/new","Request"],["/evidence","Evidence"],
  ["/court","Court"],["/vault","Vault"],["/verify","Verify"],["/docs","Docs"],
];
export function Shell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return <>
    <header className="topbar">
      <Link href="/" className="brand"><span className="brandMark">SR</span><span>StewardRail</span></Link>
      <nav className={open ? "mobileOpen" : ""}>{nav.map(([href,label]) => <Link href={href} key={href} onClick={() => setOpen(false)}>{label}</Link>)}</nav>
      <div className="headerActions"><button className="menuButton" aria-label="Open navigation" aria-expanded={open} onClick={() => setOpen(!open)}>Menu</button><WalletButton /></div>
    </header>
    <main>{children}</main>
    <TxDrawer />
  </>;
}
