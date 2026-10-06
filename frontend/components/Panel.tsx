export function Panel({ title, eyebrow, children, className="" }: { title?: string; eyebrow?: string; children: React.ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{eyebrow && <div className="eyebrow">{eyebrow}</div>}{title && <h2>{title}</h2>}{children}</section>;
}
export function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return <div className="stat"><span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div>;
}
