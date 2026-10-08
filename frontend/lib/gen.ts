export const GEN_SYMBOL = "GEN";
export const GEN_DECIMALS = 18;

export function parseGen(input: string): bigint {
  const value = input.trim();
  if (!value || !/^\d+(?:\.\d+)?$/.test(value)) throw new Error("Enter a non-negative GEN amount using digits and an optional decimal point.");
  const [whole, fraction = ""] = value.split(".");
  if (fraction.length > GEN_DECIMALS) throw new Error("GEN amounts support at most 18 decimal places.");
  const normalized = `${whole}${fraction.padEnd(GEN_DECIMALS, "0")}`.replace(/^0+(?=\d)/, "");
  return BigInt(normalized || "0");
}

export function formatGen(value: bigint | number | string): string {
  const units = typeof value === "bigint" ? value : BigInt(value);
  if (units < 0n) throw new Error("GEN amount cannot be negative.");
  const scale = 10n ** BigInt(GEN_DECIMALS);
  const whole = units / scale;
  const fraction = (units % scale).toString().padStart(GEN_DECIMALS, "0").replace(/0+$/, "");
  return fraction ? `${whole}.${fraction}` : whole.toString();
}
