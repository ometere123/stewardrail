import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { injectedProvider } from "./wallet";
import { NETWORK } from "./deployments";
import type { TxRecord } from "./types";

const readClient: any = (createClient as any)({ chain: studionet });

/** genlayer-js 1.1.8 exposes receipt fields but no isSuccessful helper. */
function successfulReceipt(receipt: any, expectedStatus: "ACCEPTED" | "FINALIZED"): boolean {
  return receipt?.statusName === expectedStatus
    && receipt?.txExecutionResultName === "FINISHED_WITH_RETURN";
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
  await client.connect("studionet");
  const call: any = { address: params.address, functionName: params.functionName, args: params.args ?? [] };
  if (params.value && params.value > 0n) call.value = params.value;
  const estimate = await client.estimateTransactionFeesForWrite(call);
  const hash = await client.writeContract({
    ...call,
    fees: { distribution: estimate.distribution, feeValue: estimate.feeValue },
  });
  params.onProgress({ phase: "submitted", hash, action: params.action, contract: params.address });
  const decided = await client.waitForDecision({ hash });
  const decidedOk = successfulReceipt(decided, "ACCEPTED");
  params.onProgress({
    phase: decidedOk ? "decided" : "failed", hash, action: params.action, contract: params.address,
    status: decided.statusName, execution: decided.txExecutionResultName,
    error: decidedOk ? undefined : `Decision did not execute successfully: ${decided.statusName} / ${decided.txExecutionResultName}`,
  });
  if (!decidedOk) throw new Error(`Transaction failed: ${decided.statusName} / ${decided.txExecutionResultName}`);
  const finalized = await client.waitForFinalization({ hash });
  const finalOk = successfulReceipt(finalized, "FINALIZED");
  const record: TxRecord = {
    phase: finalOk ? "finalized" : "failed", hash, action: params.action, contract: params.address,
    status: finalized.statusName, execution: finalized.txExecutionResultName,
    error: finalOk ? undefined : `Finalized execution failed: ${finalized.statusName} / ${finalized.txExecutionResultName}`,
  };
  params.onProgress(record);
  if (!finalOk) throw new Error(record.error);
  return finalized;
}

export async function resumeFinalization(hash: string, previous: TxRecord, onProgress: (tx: TxRecord) => void) {
  const finalized = await readClient.waitForFinalization({ hash });
  const ok = successfulReceipt(finalized, "FINALIZED");
  const next: TxRecord = {
    ...previous, hash, phase: ok ? "finalized" : "failed",
    status: finalized.statusName, execution: finalized.txExecutionResultName,
    error: ok ? undefined : `Finalized execution failed: ${finalized.statusName} / ${finalized.txExecutionResultName}`,
  };
  onProgress(next);
  if (!ok) throw new Error(next.error);
  return finalized;
}
