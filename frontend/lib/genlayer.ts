import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { injectedProvider } from "./wallet";
import { NETWORK } from "./deployments";
import type { TxRecord } from "./types";

const readClient: any = (createClient as any)({ chain: studionet });

const STATUS_BY_NUMBER: Record<string, string> = {
  "0": "UNINITIALIZED",
  "1": "PENDING",
  "2": "PROPOSING",
  "3": "COMMITTING",
  "4": "REVEALING",
  "5": "ACCEPTED",
  "6": "UNDETERMINED",
  "7": "FINALIZED",
  "8": "CANCELED",
  "9": "APPEAL_REVEALING",
  "10": "APPEAL_COMMITTING",
  "11": "READY_TO_FINALIZE",
  "12": "VALIDATORS_TIMEOUT",
  "13": "LEADER_TIMEOUT",
};

const RESULT_BY_NUMBER: Record<string, string> = {
  "0": "IDLE",
  "1": "AGREE",
  "2": "DISAGREE",
  "3": "TIMEOUT",
  "4": "DETERMINISTIC_VIOLATION",
  "5": "NO_MAJORITY",
  "6": "MAJORITY_AGREE",
  "7": "MAJORITY_DISAGREE",
};

const EXECUTION_BY_NUMBER: Record<string, string> = {
  "0": "NOT_VOTED",
  "1": "FINISHED_WITH_RETURN",
  "2": "FINISHED_WITH_ERROR",
};

function enumName(value: unknown, numericNames: Record<string, string>): string | undefined {
  if (value === undefined || value === null || value === "") return undefined;
  const text = String(value).toUpperCase();
  return numericNames[text] ?? text;
}

/**
 * genlayer-js returns decoded names on public networks, while the Studio
 * adapter can expose the underlying numeric enum or snake_case field. Keep
 * the normalization here so a receipt is never mislabelled as an unknown
 * consensus or execution result.
 */
function statusName(receipt: any): string | undefined {
  return enumName(receipt?.statusName ?? receipt?.status_name ?? receipt?.status, STATUS_BY_NUMBER);
}

function consensusName(receipt: any): string {
  const direct = enumName(receipt?.resultName ?? receipt?.result_name ?? receipt?.result, RESULT_BY_NUMBER);
  if (direct) return direct;
  return enumName(receipt?.consensus ?? receipt?.consensusResult, RESULT_BY_NUMBER) ?? "";
}

function executionName(receipt: any): string | undefined {
  const direct = enumName(
    receipt?.txExecutionResultName
      ?? receipt?.tx_execution_result_name
      ?? receipt?.txExecutionResult
      ?? receipt?.tx_execution_result,
    EXECUTION_BY_NUMBER,
  );
  if (direct) return direct;

  const leaderReceipts = receipt?.consensus_data?.leader_receipt;
  const leader = Array.isArray(leaderReceipts) ? leaderReceipts[0] : leaderReceipts;
  const leaderExecution = String(leader?.execution_result ?? leader?.executionResult ?? "").toUpperCase();
  if (leaderExecution === "SUCCESS" || leaderExecution === "FINISHED_WITH_RETURN") return "FINISHED_WITH_RETURN";
  if (leaderExecution === "ERROR" || leaderExecution === "FINISHED_WITH_ERROR") return "FINISHED_WITH_ERROR";
  return undefined;
}

function executionSucceeded(receipt: any): boolean {
  return executionName(receipt) === "FINISHED_WITH_RETURN";
}

function consensusAccepted(receipt: any): boolean {
  const status = statusName(receipt);
  if (["UNDETERMINED", "CANCELED", "VALIDATORS_TIMEOUT", "LEADER_TIMEOUT"].includes(status ?? "")) return false;
  const result = consensusName(receipt);
  return result === "MAJORITY_AGREE" || result === "AGREE";
}

function consensusUndetermined(receipt: any): boolean {
  return statusName(receipt) === "UNDETERMINED"
    || ["MAJORITY_DISAGREE", "NO_MAJORITY", "DISAGREE", "TIMEOUT"].includes(consensusName(receipt));
}

function successfulReceipt(receipt: any, expectedStatus: "ACCEPTED" | "FINALIZED"): boolean {
  return statusName(receipt) === expectedStatus
    && executionSucceeded(receipt)
    && consensusAccepted(receipt);
}

function failurePhase(receipt: any): "undetermined" | "failed" {
  return consensusUndetermined(receipt) ? "undetermined" : "failed";
}

function receiptError(receipt: any, label: string): string {
  return `${label}: status=${statusName(receipt) ?? "unknown"}, consensus=${consensusName(receipt) || "unknown"}, execution=${executionName(receipt) ?? "unknown"}`;
}

function receiptFailure(receipt: any, expectedStatus: "ACCEPTED" | "FINALIZED"): string {
  if (consensusUndetermined(receipt)) return receiptError(receipt, "Consensus remained undetermined");
  if (!consensusAccepted(receipt)) return receiptError(receipt, "Consensus decision was not accepted");
  if (!executionSucceeded(receipt)) return receiptError(receipt, "GenVM execution failed");
  if (statusName(receipt) !== expectedStatus) return receiptError(receipt, `Transaction did not reach ${expectedStatus}`);
  return receiptError(receipt, "Transaction did not complete successfully");
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
    const child = { hash, phase: consensusAccepted(decided) ? "decided" as const : failurePhase(decided), status: statusName(decided), consensus: consensusName(decided), execution: executionName(decided), error: consensusAccepted(decided) ? undefined : receiptFailure(decided, "ACCEPTED") };
    const index = children.findIndex((item) => item.hash === hash);
    if (index >= 0) children[index] = child; else children.push(child);
    onProgress({ ...base, phase: child.phase === "undetermined" ? "undetermined" : "decided", children });
    const final = await client.waitForTransactionReceipt({ hash, status: "FINALIZED", fullTransaction: true });
    const ok = successfulReceipt(final, "FINALIZED");
    const finalChild = { hash, phase: ok ? "finalized" as const : failurePhase(final), status: statusName(final), consensus: consensusName(final), execution: executionName(final), error: ok ? undefined : receiptFailure(final, "FINALIZED") };
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
    status: statusName(decided), consensus: consensusName(decided), execution: executionName(decided),
    error: decidedOk ? undefined : receiptFailure(decided, "ACCEPTED"),
  });
  if (!decidedOk) throw new Error(receiptFailure(decided, "ACCEPTED"));
  const finalized = await client.waitForTransactionReceipt({ hash, status: "FINALIZED", fullTransaction: true });
  const finalOk = successfulReceipt(finalized, "FINALIZED");
  const record: TxRecord = {
    phase: finalOk ? "finalized" : failurePhase(finalized), hash, action: params.action, contract: params.address,
    status: statusName(finalized), consensus: consensusName(finalized), execution: executionName(finalized),
    error: finalOk ? undefined : receiptFailure(finalized, "FINALIZED"),
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
    status: statusName(finalized), consensus: consensusName(finalized), execution: executionName(finalized),
    error: ok ? undefined : receiptFailure(finalized, "FINALIZED"),
  };
  onProgress(next);
  if (!ok) throw new Error(next.error);
  const settled = await settleTriggered(readClient, hash, next, onProgress);
  if (settled.phase === "failed") throw new Error(settled.error);
  return finalized;
}
