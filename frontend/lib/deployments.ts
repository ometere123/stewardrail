export const NETWORK = {
  name: "Studionet",
  chainId: 61999,
  chainHex: "0xF22F",
  rpc: "https://studio.genlayer.com/api",
  explorer: "https://explorer-studio.genlayer.com",
} as const;

// Filled from deploy/deployments.json after the clean 61999 deployment.
export const DEPLOYMENTS = {
  charter: "",
  registry: "",
  court: "",
  guard: "",
  vault: "",
} as const;

export const deployed = Object.values(DEPLOYMENTS).every(Boolean);
