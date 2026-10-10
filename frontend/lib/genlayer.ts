import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { injectedProvider } from "./wallet";
import { NETWORK } from "./deployments";
import type { TxRecord } from "./types";

const readClient: any = (createClient as any)({ chain: studionet });

/** genlayer-js 1.1.8 exposes receipt fields but no success helper. */
function consensusName(receipt: any): string {
  return String(receipt?.resultName ?? receipt?.result ?? "").toUpperCase();
}

function executionSucceeded(receipt: any): boolean {
  return receipt?.txExecutionResultName === "FINISHED_WITH_RETURN";
}

function consensusAccepted(receipt: any): boolean {
  const result = consensusName(receipt);
  return result === "MAJORITY_AGREE" || result === "AGREE";
}

function consensusUndetermined(receipt: any): boolean {
  return receipt?.statusName === "UNDETERMINED"
    || ["MAJORITY_DISAGREE", "NO_MAJORITY", "DISAGREE", "TIMEOUT"].includes(consensusName(receipt));
}

function successfulReceipt(receipt: any, expectedStatus: "ACCEPTED" | "FINALIZED"): boolean {
  return receipt?.statusName === expectedStatus
    && executionSucceeded(receipt)
    && consensusAccepted(receipt);
}

function failurePhase(receipt: any): "undetermined" | "failed" {
  return consensusUndetermined(receipt) ? "undetermined" : "failed";
}

function receiptError(receipt: any, label: string): string {
  return `${label}: status=${receipt?.statusName ?? "unknown"}, consensus=${consensusName(receipt) || "unknown"}, execution=${receipt?.txExecutionResultName ?? "unknown"}`;
}

async function settleTriggered(client: any, parentHash: string, base: TxRecord, onProgress: (tx: TxRecord) => void): Promise<TxRecord> {
  const seen = new Set<string>();
  const children = [...(base.children ?? [])];
  const visit = async (hash: string, depth: number): Promise<boolean> => {
    if (depth > 4 || seen.has(hash)) return true;
    seen.add(hash);
    let decided: any;
    try {
      decided = await client.waitForTransactionReceipt({ hash, status: "ACCEPTED", fullTransaction: true });
    } catch (error: any) {
      children.push({ hash, phase: "failed", error: String(error?.message ?? error) });
      return false;
    }
    const child = { hash, phase: consensusAccepted(decided) ? "decided" as const : failurePhase(decided), status: decided?.statusName, consensus: consensusName(decided), execution: decided?.txExecutionResultName, error: consensusAccepted(decided) ? undefined : receiptError(decided, "Child consensus not accepted") };
    const index = children.findIndex((item) => item.hash === hash);
    if (index >= 0) children[index] = child; else children.push(child);
    onProgress({ ...base, phase: child.phase === "undetermined" ? "undetermined" : "decided", children });
    const final = await client.waitForTransactionReceipt({ hash, status: "FINALIZED", fullTransaction: true });
    const ok = successfulReceipt(final, "FINALIZED");
    const finalChild = { hash, phase: ok ? "finalized" as const : failurePhase(final), status: final?.statusName, consensus: consensusName(final), execution: final?.txExecutionResultName, error: ok ? undefined : receiptError(final, "Child finalization not successful") };
    const finalIndex = children.findIndex((item) => item.hash === hash);
    if (finalIndex >= 0) children[finalIndex] = finalChild; else children.push(finalChild);
    onProgress({ ...base, phase: ok ? "finalized" : finalChild.phase, children, error: ok ? base.error : finalChild.error });
    if (!ok || !consensusAccepted(decided) || !executionSucceeded(decided)) return false;
    let nested: string[] = [];
    try { nested = await client.getTriggeredTransactionIds({ hash }); } catch { nested = []; }
    let all = true;
    for (const nestedHash of nested) all = (await visit(String(nestedHash), depth + 1)) && all;
    return all;
  };
  let roots: string[] = [];
  try { roots = await client.getTriggeredTransactionIds({ hash: parentHash }); } catch { roots = []; }
  let all = true;
  for (const hash of roots) all = (await visit(String(hash), 1)) && all;
  const final: TxRecord = { ...base, phase: all ? "finalized" : (children.some((child) => child.phase === "undetermined") ? "undetermined" : "failed"), children, error: all ? base.error : "A triggered transaction was not accepted and finalized successfully; retry reconciliation from the recorded parent." };
  onProgress(final);
  return final;
}

export async function readContract(address: string, functionName: string, args: unknown[] = []) {
  if (!address) throw new Error("Contract address is not configured yet.");
  return readClient.readContract({ address, functionName, args });
}

export async function readJson<T>(address: string, functionName: string, args: unknown[] = []): Promise<T> {
  const raw = await readContract(address, functionName, args);
  return typeof raw === "string" ? JSON.parse(raw) as T : raw as T;
}

export async function writeContract(params: {
  address: string;
  functionName: string;
  args?: unknown[];
  value?: bigint;
  account: string;
  action: string;
  onProgress: (tx: TxRecord) => void;
}) {
  const p = injectedProvider();
  const chain = Number(BigInt(await p.request({ method: "eth_chainId" })));
  if (chain !== NETWORK.chainId) throw new Error(`Wrong network. StewardRail only signs on chain ${NETWORK.chainId}.`);
  if (!params.address) throw new Error("Contract address is not configured yet.");
  const client: any = (createClient as any)({ chain: studionet, account: params.account, provider: p });
  const hash = await client.writeContract({
    address: params.address,
    functionName: params.functionName,
    args: params.args ?? [],
    value: params.value ?? 0n,
  });
  params.onProgress({ phase: "submitted", hash, action: params.action, contract: params.address });
  const decided = await client.waitForTransactionReceipt({ hash, status: "ACCEPTED", fullTransaction: true });
  const decidedOk = successfulReceipt(decided, "ACCEPTED");
  params.onProgress({
    phase: decidedOk ? "decided" : failurePhase(decided), hash, action: params.action, contract: params.address,
    status: decided.statusName, consensus: consensusName(decided), execution: decided.txExecutionResultName,
    error: decidedOk ? undefined : receiptError(decided, "Consensus decision not accepted"),
  });
  if (!decidedOk) throw new Error(receiptError(decided, "Transaction did not reach accepted consensus"));
  const finalized = await client.waitForTransactionReceipt({ hash, status: "FINALIZED", fullTransaction: true });
  const finalOk = successfulReceipt(finalized, "FINALIZED");
  const record: TxRecord = {
    phase: finalOk ? "finalized" : failurePhase(finalized), hash, action: params.action, contract: params.address,
    status: finalized.statusName, consensus: consensusName(finalized), execution: finalized.txExecutionResultName,
    error: finalOk ? undefined : receiptError(finalized, "Finalized transaction not successful"),
  };
  params.onProgress(record);
  if (!finalOk) throw new Error(record.error);
  const settled = await settleTriggered(client, hash, record, params.onProgress);
  if (settled.phase === "failed") throw new Error(settled.error);
  return finalized;
}

export async function resumeFinalization(hash: string, previous: TxRecord, onProgress: (tx: TxRecord) => void) {
  const finalized = await readClient.waitForTransactionReceipt({ hash, status: "FINALIZED", fullTransaction: true });
  const ok = successfulReceipt(finalized, "FINALIZED");
  const next: TxRecord = {
    ...previous, hash, phase: ok ? "finalized" : failurePhase(finalized),
    status: finalized.statusName, consensus: consensusName(finalized), execution: finalized.txExecutionResultName,
    error: ok ? undefined : receiptError(finalized, "Finalized transaction not successful"),
  };
  onProgress(next);
  if (!ok) throw new Error(next.error);
  const settled = await settleTriggered(readClient, hash, next, onProgress);
  if (settled.phase === "failed") throw new Error(settled.error);
  return finalized;
}
