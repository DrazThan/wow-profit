const STATE_STYLES = {
  fresh: 'bg-green-900/50 text-green-300 border-green-700',
  stale: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
  old: 'bg-red-900/50 text-red-300 border-red-700',
  no_data: 'bg-gray-800 text-wow-gray border-wow-border',
}

const STATE_LABELS = {
  fresh: 'Fresh',
  stale: 'Stale',
  old: 'Old data',
  no_data: 'No data',
}

export default function DataFreshnessPill({ state, ageHours, onClick }) {
  const style = STATE_STYLES[state] || STATE_STYLES.no_data
  const label = STATE_LABELS[state] || 'Unknown'
  const age = ageHours != null
    ? ageHours < 1
      ? `${Math.round(ageHours * 60)}m ago`
      : `${ageHours.toFixed(1)}h ago`
    : null

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium transition-opacity hover:opacity-80 ${style}`}
      title={state === 'no_data' ? 'No scan data uploaded yet' : `Last scan: ${age}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {label}
      {age && <span className="opacity-70">{age}</span>}
    </button>
  )
}
