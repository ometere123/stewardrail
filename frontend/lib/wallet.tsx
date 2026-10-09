"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { NETWORK } from "./deployments";

type WalletState = {
  address: string;
  chainId: number | null;
  connected: boolean;
  correctNetwork: boolean;
  connect: () => Promise<void>;
  switchNetwork: () => Promise<void>;
  disconnect: () => void;
};

const WalletContext = createContext<WalletState | null>(null);

function provider(): any {
  if (typeof window === "undefined") return null;
  return (window as any).ethereum ?? null;
}

function parseChain(value: string | number | null): number | null {
  if (value === null) return null;
  if (typeof value === "number") return value;
  try { return Number(BigInt(value)); } catch { return null; }
}

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const [address, setAddress] = useState("");
  const [chainId, setChainId] = useState<number | null>(null);
  const [disconnected, setDisconnected] = useState(false);

  const refresh = useCallback(async () => {
    const p = provider();
    if (!p) return;
    const [accounts, chain] = await Promise.all([
      p.request({ method: "eth_accounts" }),
      p.request({ method: "eth_chainId" }),
    ]);
    if (localStorage.getItem("stewardrail.wallet.disconnected") === "1") return;
    setAddress(Array.isArray(accounts) && accounts[0] ? String(accounts[0]) : "");
    setChainId(parseChain(chain));
  }, []);

  useEffect(() => {
    const p = provider();
    if (!p) return;
    refresh().catch(() => undefined);
    const accountsChanged = (accounts: string[]) => {
      // An explicit app-level disconnect must not be undone by the wallet's
      // automatic accountsChanged notification. The next explicit Connect
      // action clears this local preference.
      if (localStorage.getItem("stewardrail.wallet.disconnected") === "1") {
        setAddress("");
        return;
      }
      setAddress(accounts?.[0] ?? "");
    };
    const chainChanged = (chain: string) => setChainId(parseChain(chain));
    p.on?.("accountsChanged", accountsChanged);
    p.on?.("chainChanged", chainChanged);
    return () => {
      p.removeListener?.("accountsChanged", accountsChanged);
      p.removeListener?.("chainChanged", chainChanged);
    };
  }, [refresh]);

  const connect = useCallback(async () => {
    const p = provider();
    if (!p) throw new Error("No injected EIP-1193 wallet found.");
    const accounts = await p.request({ method: "eth_requestAccounts" });
    setDisconnected(false);
    localStorage.removeItem("stewardrail.wallet.disconnected");
    setAddress(String(accounts?.[0] ?? ""));
    setChainId(parseChain(await p.request({ method: "eth_chainId" })));
  }, []);

  const switchNetwork = useCallback(async () => {
    const p = provider();
    if (!p) throw new Error("No injected EIP-1193 wallet found.");
    try {
      await p.request({ method: "wallet_switchEthereumChain", params: [{ chainId: NETWORK.chainHex }] });
    } catch (error: any) {
      if (error?.code !== 4902) throw error;
      await p.request({ method: "wallet_addEthereumChain", params: [{
        chainId: NETWORK.chainHex,
        chainName: NETWORK.name,
        nativeCurrency: { name: "GEN", symbol: "GEN", decimals: 18 },
        rpcUrls: [NETWORK.rpc],
        blockExplorerUrls: [NETWORK.explorer],
      }] });
    }
    setChainId(parseChain(await p.request({ method: "eth_chainId" })));
  }, []);

  const disconnect = useCallback(() => {
    localStorage.setItem("stewardrail.wallet.disconnected", "1");
    setDisconnected(true);
    setAddress("");
  }, []);
  const value = useMemo(() => ({
    address, chainId, connected: Boolean(address), correctNetwork: chainId === NETWORK.chainId,
    connect, switchNetwork, disconnect,
  }), [address, chainId, connect, switchNetwork, disconnect]);

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
}

export function useWallet() {
  const value = useContext(WalletContext);
  if (!value) throw new Error("useWallet must be inside WalletProvider");
  return value;
}

export function injectedProvider(): any {
  const p = provider();
  if (!p) throw new Error("No injected EIP-1193 wallet found.");
  return p;
}
