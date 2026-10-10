import fs from "node:fs";
import path from "node:path";
const root = process.cwd();
const walk = (dir) => fs.readdirSync(dir, {withFileTypes:true}).flatMap((e) => {
  const p = path.join(dir, e.name); return e.isDirectory() ? walk(p) : [p];
});
const files = walk(path.join(root, "app")).concat(walk(path.join(root, "components")), walk(path.join(root, "lib")));
const text = files.filter(f => /\.(ts|tsx)$/.test(f)).map(f => fs.readFileSync(f,"utf8")).join("\n").toLowerCase();
for (const token of ["walletconnect", "@reown", "privy", "supabase", "firebase"]) {
  if (text.includes(token)) throw new Error(`forbidden dependency marker: ${token}`);
}
if (!text.includes("61999")) throw new Error("61999 hard gate missing");
if (!text.includes(".ethereum") || !text.includes("eth_requestaccounts")) throw new Error("injected wallet path missing");
if (!text.includes("accountschanged") || !text.includes("chainchanged")) throw new Error("wallet event handling missing");
if (!text.includes("localstorage") || !text.includes("resumefinalization")) throw new Error("transaction refresh recovery missing");
if (!text.includes("gettriggeredtransactionids") || !text.includes("children")) throw new Error("nested triggered transaction tracking missing");
if (!text.includes("parsegen") || !text.includes("formatgen")) throw new Error("exact GEN conversion utilities missing");
if (!text.includes("disconnect")) throw new Error("explicit disconnect control missing");
if (text.includes("wallet_getsnaps") || text.includes("wallet_requestsnaps") || text.includes("wallet_invokesnap")) throw new Error("Snap wallet methods must not be used");
if (text.includes("client.connect(\"studionet\")") || text.includes("waitfordecision") || text.includes("waitforfinalization")) throw new Error("unsupported SDK wallet/finality helpers remain");
if (!text.includes("resultname") || !text.includes("majority_agree") || !text.includes("undetermined")) throw new Error("consensus result handling missing");
if (!text.includes("status_by_number") || !text.includes("execution_by_number") || !text.includes("leader?.execution_result")) throw new Error("numeric Studio receipt normalization missing");
if (text.includes("amount (wei)") || text.includes("fund amount (wei)")) throw new Error("raw wei label remains in the primary UI");
const evidence = fs.readFileSync(path.join(root, "app", "evidence", "page.tsx"), "utf8").toLowerCase();
if (!evidence.includes("const [issuer,setissuer]") || !evidence.includes("args={[number(spend),issuer")) throw new Error("evidence attachment must bind the explicit attested issuer");
const court = fs.readFileSync(path.join(root, "app", "court", "page.tsx"), "utf8");
if (!court.includes('id="challenge-id"') || !court.includes('const [challengeId')) throw new Error("court progression must use a dedicated challenge ID");
if (!court.includes('className="actionGrid"') || !court.includes('className="full challengeProgression"')) throw new Error("court challenge progression must be a full-width responsive action grid");
if (!court.includes('method="reconcile_open_challenge" args={[challengeArg]}') || !court.includes('method="resolve_challenge" args={[DEPLOYMENTS.guard,challengeArg,DEPLOYMENTS.bondVault]')) throw new Error("court challenge actions must pass the challenge ID");
console.log("frontend static test: PASS");
