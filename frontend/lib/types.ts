export type TxPhase = "idle" | "submitted" | "decided" | "undetermined" | "finalized" | "failed";
export type ChildTxRecord = { hash: string; phase: TxPhase; status?: string; consensus?: string; execution?: string; error?: string };
export type TxRecord = {
  phase: TxPhase;
  hash?: string;
  action?: string;
  contract?: string;
  status?: string;
  consensus?: string;
  execution?: string;
  error?: string;
  children?: ChildTxRecord[];
};
