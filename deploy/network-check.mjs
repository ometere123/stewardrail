const RPC = "https://studio.genlayer.com/api";
const EXPECTED = 61999;
const body = { jsonrpc: "2.0", id: 1, method: "eth_chainId", params: [] };
const res = await fetch(RPC, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
if (!res.ok) throw new Error(`RPC HTTP ${res.status}`);
const json = await res.json();
const got = Number(BigInt(json.result));
if (got !== EXPECTED) throw new Error(`WRONG NETWORK: expected ${EXPECTED}, got ${got}`);
console.log(`network check: PASS (${got}) ${RPC}`);
