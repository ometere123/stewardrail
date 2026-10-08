export const NETWORK = {
  name: "Studionet",
  chainId: 61999,
  chainHex: "0xF22F",
  rpc: "https://studio.genlayer.com/api",
  explorer: "https://explorer-studio.genlayer.com",
} as const;

// Filled from deploy/deployments.json after the clean 61999 deployment.
export const DEPLOYMENTS = {
  charter: "0xa7b510DdE3F57cbCCB1802CFD2ae85a756Ca4EA5",
  registry: "0x46127eaFA44532FF273901C586F36C0544E9E15C",
  court: "0xC97a65B46bceF1ac2Fb0176DFBC8ba93929c33Bf",
  guard: "0x8723731b86E782F9086a92166E8E004504Da25D4",
  vault: "0xff8b6C5eaEd9eD71555688efB1A15F41DF997436",
} as const;

export const deployed = Object.values(DEPLOYMENTS).every(Boolean);
