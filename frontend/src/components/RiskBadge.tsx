export default function RiskBadge({ level }: { level?: string }) {
  const lvl = (level || 'NONE').toUpperCase()
  return <span className={`badge badge-${lvl}`}>{lvl}</span>
}
