import { useState } from 'react'
import { useRealm } from '../hooks/useRealm'

const POPULAR_REALMS = [
  'faerlina', 'benediction', 'whitemane', 'grobbulus',
  'sulfuras', 'earthfury', 'mankrik', 'skyfury',
]

export default function RealmSelector() {
  const { realm, faction, update } = useRealm()
  const [editRealm, setEditRealm] = useState(realm)

  const handleApply = () => {
    if (editRealm.trim()) update(editRealm.trim().toLowerCase(), faction)
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <select
        value={editRealm}
        onChange={(e) => setEditRealm(e.target.value)}
        className="input w-40"
      >
        {POPULAR_REALMS.map((r) => (
          <option key={r} value={r}>{r}</option>
        ))}
      </select>

      <input
        className="input w-32"
        placeholder="Custom realm"
        value={editRealm}
        onChange={(e) => setEditRealm(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleApply()}
      />

      <div className="flex rounded overflow-hidden border border-wow-border">
        {['horde', 'alliance'].map((f) => (
          <button
            key={f}
            onClick={() => update(realm, f)}
            className={`px-3 py-1.5 text-sm capitalize transition-colors duration-100 ${
              faction === f
                ? f === 'horde'
                  ? 'bg-red-900 text-red-200'
                  : 'bg-blue-900 text-blue-200'
                : 'bg-wow-brown text-wow-gray hover:text-wow-parchment'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <button onClick={handleApply} className="btn-gold">
        Apply
      </button>
    </div>
  )
}
