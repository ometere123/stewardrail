import Link from "next/link";
import { WalletButton } from "./WalletButton";
import { TxDrawer } from "./TxDrawer";

const nav = [
  ["/workspace","Workspace"],["/spends/new","Request"],["/evidence","Evidence"],
  ["/court","Court"],["/vault","Vault"],["/verify","Verify"],["/docs","Docs"],
];
export function Shell({ children }: { children: React.ReactNode }) {
  return <>
    <header className="topbar">
      <Link href="/" className="brand"><span className="brandMark">SR</span><span>StewardRail</span></Link>
      <nav>{nav.map(([href,label]) => <Link href={href} key={href}>{label}</Link>)}</nav>
      <WalletButton />
    </header>
    <main>{children}</main>
    <TxDrawer />
  </>;
}
