export type TxPhase = "idle" | "submitted" | "decided" | "finalized" | "failed";
export type TxRecord = {
  phase: TxPhase;
  hash?: string;
  action?: string;
  contract?: string;
  status?: string;
  execution?: string;
  error?: string;
};
