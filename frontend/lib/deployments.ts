export const NETWORK = {
  name: "Studionet",
  chainId: 61999,
  chainHex: "0xF22F",
  rpc: "https://studio.genlayer.com/api",
  explorer: "https://explorer-studio.genlayer.com",
} as const;

// Filled from deploy/deployments.json after the clean 61999 deployment.
export const DEPLOYMENTS = {
  charter: "0x44B3aBA05776236bB30509811B7242c391dcA77B",
  registry: "0xfe8E20e4781EaE24bfa3D3a8c1B17A6A5E4d77ec",
  court: "0xCDff705BaCD83512FbC6Dd1441A4b5afA6a81Ee6",
  guard: "0x7Bcf0ee85c4BeDA5CA51FC69D8ee5a673c5d95EB",
  vault: "0x353F90CFa7294e922F5AA91027245086320A84AF",
} as const;

export const deployed = Object.values(DEPLOYMENTS).every(Boolean);
