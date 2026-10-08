export const NETWORK = {
  name: "Studionet",
  chainId: 61999,
  chainHex: "0xF22F",
  rpc: "https://studio.genlayer.com/api",
  explorer: "https://explorer-studio.genlayer.com",
} as const;

// Filled from deploy/deployments.json after the clean 61999 deployment.
export const DEPLOYMENTS = {
  charter: "0xDCC1D6c08CFff25e793dd608e01218c597Ed9e31",
  registry: "0x93938Fad09F0133BDF8e10f2F447E498B59165a7",
  court: "0xD6112e5B534E4A3029e11fc9aa42A0d7D1089Fc2",
  guard: "0x00a790c46Ae285F2431E70b97c95Ec910f63A1d4",
  vault: "0xABBe722224e5C9Ab7B9a6fbB24C9AF92D454F30f",
} as const;

export const deployed = Object.values(DEPLOYMENTS).every(Boolean);
