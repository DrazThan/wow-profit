import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import DataFreshnessPill from '../components/DataFreshnessPill'
import UploadZone from '../components/UploadZone'
import { useRealm } from '../hooks/useRealm'

function UploadHistory({ realm, faction, refreshKey }) {
  const [history, setHistory] = useState([])

  useEffect(() => {
    api.getUploadHistory({ realm, faction, limit: 10 })
      .then(r => setHistory(r.data))
      .catch(() => {})
  }, [realm, faction, refreshKey])

  if (!history.length) return null

  return (
    <div className="panel space-y-2">
      <h3 className="text-wow-gold-dark text-sm font-medium">Recent Uploads</h3>
      <div className="divide-y divide-wow-border/30 text-sm">
        {history.map((log) => (
          <div key={log.id} className="py-2 flex items-center justify-between gap-4">
            <div>
              <span className="text-wow-parchment">{log.filename}</span>
              <span className="text-wow-gray ml-2 text-xs capitalize">{log.upload_source}</span>
            </div>
            <div className="text-right shrink-0">
              <p className="text-wow-gray text-xs">
                {log.items_imported.toLocaleString()} items · {log.realm} - {log.faction}
              </p>
              <p className="text-wow-border text-xs">
                {new Date(log.uploaded_at).toLocaleString()}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Upload() {
  const { realm, faction } = useRealm()
  const [freshness, setFreshness] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const loadFreshness = useCallback(() => {
    api.getUploadStatus({ realm, faction })
      .then(r => setFreshness(r.data))
      .catch(() => setFreshness({ state: 'no_data' }))
  }, [realm, faction])

  useEffect(() => { loadFreshness() }, [loadFreshness])

  const handleSuccess = useCallback(() => {
    setRefreshKey(k => k + 1)
    loadFreshness()
  }, [loadFreshness])

  return (
    <div className="p-6 space-y-6 max-w-2xl">
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-wow-gold text-2xl font-cinzel">Upload Scan Data</h1>
        {freshness && (
          <DataFreshnessPill
            state={freshness.state}
            ageHours={freshness.age_hours}
          />
        )}
      </div>

      <div className="panel space-y-4">
        <h2 className="text-wow-gold-dark font-medium">How to scan</h2>
        <ol className="text-sm text-wow-parchment space-y-2 list-decimal list-inside">
          <li>Open the Auction House in-game.</li>
          <li>
            Click <strong className="text-wow-gold">Full Scan</strong> in the Auctionator UI
            (or type <code className="text-wow-gold">/atr scan</code>).
          </li>
          <li>Wait ~30 seconds for the scan to complete.</li>
          <li>Type <code className="text-wow-gold">/reload</code> or log out to flush data to disk.</li>
          <li>
            Find your file at:
            <ul className="mt-1 ml-4 space-y-0.5 text-wow-gray text-xs">
              <li>
                <strong className="text-wow-parchment">Windows:</strong>{' '}
                <code>C:\Program Files (x86)\World of Warcraft\_classic_\WTF\Account\&lt;ACCOUNT&gt;\SavedVariables\Auctionator.lua</code>
              </li>
              <li>
                <strong className="text-wow-parchment">Mac:</strong>{' '}
                <code>~/Library/Application Support/World of Warcraft/_classic_/WTF/Account/&lt;ACCOUNT&gt;/SavedVariables/Auctionator.lua</code>
              </li>
            </ul>
          </li>
          <li>Drop the file below.</li>
        </ol>
      </div>

      <div className="panel">
        <UploadZone onSuccess={handleSuccess} />
      </div>

      <UploadHistory realm={realm} faction={faction} refreshKey={refreshKey} />
    </div>
  )
}
