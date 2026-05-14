import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useRealm } from '../hooks/useRealm'

export default function RealmSelector() {
  const { realm, faction, update } = useRealm()
  const [uploadedRealms, setUploadedRealms] = useState([])
  const [customRealm, setCustomRealm] = useState('')

  useEffect(() => {
    api.getUploadedRealms()
      .then(r => setUploadedRealms(r.data || []))
      .catch(() => {})
  }, [])

  const uploadedRealmNames = uploadedRealms.map(r => r.realm)
  const hasCustom = realm && !uploadedRealmNames.includes(realm)

  const handleRealmChange = (e) => {
    const val = e.target.value
    if (val === '__custom__') return
    update(val, faction)
    setCustomRealm('')
  }

  const handleCustomApply = () => {
    const val = customRealm.trim().toLowerCase()
    if (val) update(val, faction)
  }

  const handleFaction = (f) => update(realm, f)

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <select
        value={uploadedRealmNames.includes(realm) ? realm : '__custom__'}
        onChange={handleRealmChange}
        className="input w-44"
      >
        {uploadedRealms.length === 0 && (
          <option value="faerlina">faerlina</option>
        )}
        {uploadedRealms.map(r => (
          <option key={`${r.realm}-${r.faction}`} value={r.realm}>
            {r.realm} ({r.faction})
          </option>
        ))}
        {hasCustom && (
          <option value="__custom__">{realm} (custom)</option>
        )}
        <option value="__custom__">Other realm…</option>
      </select>

      {(uploadedRealms.length === 0 || hasCustom || !uploadedRealmNames.includes(realm)) && (
        <input
          className="input w-32"
          placeholder="Realm name"
          value={customRealm}
          onChange={e => setCustomRealm(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleCustomApply()}
        />
      )}

      <div className="flex rounded overflow-hidden border border-wow-border">
        {['horde', 'alliance'].map((f) => (
          <button
            key={f}
            onClick={() => handleFaction(f)}
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

      {customRealm && (
        <button onClick={handleCustomApply} className="btn-gold">
          Apply
        </button>
      )}
    </div>
  )
}
