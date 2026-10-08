export const NETWORK = {
  name: "Studionet",
  chainId: 61999,
  chainHex: "0xF22F",
  rpc: "https://studio.genlayer.com/api",
  explorer: "https://explorer-studio.genlayer.com",
} as const;

// Filled from deploy/deployments.json after the clean 61999 deployment.
export const DEPLOYMENTS = {
  charter: "0x1e8D48Ace8Aca0DC1D61b5dEdf71c70Fc47dFf39",
  registry: "0x97C06c5216D87Bb46E98Ad24e9e61188019c92c5",
  court: "0x1Aa4872A40B68Ae9F9AB500e21556DAccD74989C",
  guard: "0x26f452a6e8b079D0d31Db4bAa7f7731Dfe114474",
  vault: "0x537D02445BBABD9Af37083f04Db3EEE19cDd7938",
} as const;

export const deployed = Object.values(DEPLOYMENTS).every(Boolean);
