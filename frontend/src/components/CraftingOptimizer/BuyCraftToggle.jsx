export default function BuyCraftToggle({ mode, onSet, hasCraft }) {
  if (!hasCraft) {
    return (
      <span className="text-xs text-wow-gray border border-wow-border/50 rounded px-2 py-0.5">
        Buy only
      </span>
    )
  }

  const isForced = mode.startsWith('forced_')
  const active = mode.replace('forced_', '')

  return (
    <div className="flex items-center gap-1">
      {isForced && (
        <button onClick={() => onSet('auto')} className="text-xs text-wow-gray hover:text-wow-gold px-1.5 py-0.5 border border-wow-border/50 rounded">
          Auto
        </button>
      )}
      <div className="flex rounded overflow-hidden border border-wow-border text-xs">
        <button
          onClick={() => onSet('buy')}
          className={`px-2 py-0.5 transition-colors ${
            active === 'buy' ? 'bg-wow-gold text-wow-brown font-semibold' : 'text-wow-gray hover:text-wow-parchment'
          }`}
        >
          Buy
        </button>
        <button
          onClick={() => onSet('craft')}
          className={`px-2 py-0.5 transition-colors ${
            active === 'craft' ? 'bg-wow-green/80 text-wow-brown font-semibold' : 'text-wow-gray hover:text-wow-parchment'
          }`}
        >
          Craft
        </button>
      </div>
    </div>
  )
}
