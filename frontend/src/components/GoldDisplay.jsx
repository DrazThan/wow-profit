export default function GoldDisplay({ copper, className = '' }) {
  if (copper == null || copper === 0) return <span className={`text-wow-gray ${className}`}>—</span>

  const abs = Math.abs(copper)
  const sign = copper < 0 ? '-' : ''
  const g = Math.floor(abs / 10000)
  const s = Math.floor((abs % 10000) / 100)
  const c = abs % 100

  return (
    <span className={`inline-flex items-center gap-1 font-mono text-sm ${className}`}>
      {sign && <span className="text-wow-red">{sign}</span>}
      {g > 0 && (
        <span>
          <span className="text-wow-gold font-semibold">{g}</span>
          <span className="text-wow-gold-dark text-xs">g</span>
        </span>
      )}
      {(g > 0 || s > 0) && (
        <span>
          <span className="text-wow-common">{s.toString().padStart(g > 0 ? 2 : 1, '0')}</span>
          <span className="text-wow-gray text-xs">s</span>
        </span>
      )}
      <span>
        <span className="text-amber-600">{c.toString().padStart(2, '0')}</span>
        <span className="text-wow-gray text-xs">c</span>
      </span>
    </span>
  )
}
