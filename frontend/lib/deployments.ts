const requireValue = (name: string, value: string | undefined): string => {
  if (!value?.trim()) throw new Error(`Missing required public configuration: ${name}`);
  return value.trim();
};
const address = (name: string, value: string | undefined): string => {
  const result = requireValue(name, value);
  if (!/^0x[0-9a-fA-F]{40}$/.test(result)) throw new Error(`Invalid public contract address: ${name}`);
  return result;
};
const networkName = requireValue("NEXT_PUBLIC_GENLAYER_NETWORK", process.env.NEXT_PUBLIC_GENLAYER_NETWORK);
const chainId = Number(requireValue("NEXT_PUBLIC_GENLAYER_CHAIN_ID", process.env.NEXT_PUBLIC_GENLAYER_CHAIN_ID));
const rpc = requireValue("NEXT_PUBLIC_GENLAYER_RPC", process.env.NEXT_PUBLIC_GENLAYER_RPC);
const explorer = requireValue("NEXT_PUBLIC_GENLAYER_EXPLORER", process.env.NEXT_PUBLIC_GENLAYER_EXPLORER);
if (!Number.isInteger(chainId) || chainId !== 61999) throw new Error("StewardRail frontend only supports Studionet 61999");
if (!/^https:\/\//.test(rpc) || !/^https:\/\//.test(explorer)) throw new Error("Public RPC and explorer must use HTTPS");
export const NETWORK = { name: networkName, chainId, chainHex: "0xF22F", rpc, explorer } as const;
export const DEPLOYMENTS = {
  charter: address("NEXT_PUBLIC_STEWARD_CHARTER", process.env.NEXT_PUBLIC_STEWARD_CHARTER),
  registry: address("NEXT_PUBLIC_EVIDENCE_REGISTRY", process.env.NEXT_PUBLIC_EVIDENCE_REGISTRY),
  court: address("NEXT_PUBLIC_STEWARD_COURT", process.env.NEXT_PUBLIC_STEWARD_COURT),
  guard: address("NEXT_PUBLIC_STEWARD_GUARD", process.env.NEXT_PUBLIC_STEWARD_GUARD),
  vault: address("NEXT_PUBLIC_STEWARD_VAULT", process.env.NEXT_PUBLIC_STEWARD_VAULT),
} as const;
export const deployed = true;
