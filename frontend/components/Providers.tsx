"use client";
import { WalletProvider } from "@/lib/wallet";
import { TxProvider } from "@/lib/tx";
export function Providers({ children }: { children: React.ReactNode }) {
  return <WalletProvider><TxProvider>{children}</TxProvider></WalletProvider>;
}
