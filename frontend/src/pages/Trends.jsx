import { useCallback, useState } from 'react'
import { api } from '../api/client'
import GoldDisplay from '../components/GoldDisplay'
import LoadingSpinner, { ErrorState } from '../components/LoadingSpinner'
import PriceChart from '../components/PriceChart'
import RealmSelector from '../components/RealmSelector'
import { useAHData } from '../hooks/useAHData'
import { useItemSearch } from '../hooks/useItemSearch'
import { useRealm } from '../hooks/useRealm'

export default function Trends() {
  const { realm, faction } = useRealm()
  const [selectedItem, setSelectedItem] = useState(null)
  const [days, setDays] = useState(14)
  const { query, setQuery, results } = useItemSearch()
  const [showResults, setShowResults] = useState(false)

  const fetchTrends = useCallback(
    () => selectedItem
      ? api.getTrends(selectedItem.itemId, { realm, faction, days }).then(r => r.data)
      : Promise.resolve(null),
    [selectedItem, realm, faction, days]
  )
  const { data: trends, loading, error } = useAHData(fetchTrends, [selectedItem, realm, faction, days])

  const selectItem = (item) => {
    setSelectedItem(item)
    setQuery(item.name)
    setShowResults(false)
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-wow-gold text-2xl font-cinzel">Price Trends</h1>
        <RealmSelector />
      </div>

      <div className="panel flex flex-wrap items-end gap-3">
        <div className="relative flex-1 min-w-48">
          <label className="text-xs text-wow-gray block mb-1">Search Item</label>
          <input
            className="input"
            placeholder="Type item name..."
            value={query}
            onChange={e => { setQuery(e.target.value); setShowResults(true) }}
            onFocus={() => setShowResults(true)}
          />
          {showResults && results.length > 0 && (
            <ul className="absolute z-20 top-full left-0 right-0 mt-1 bg-wow-brown border border-wow-border rounded shadow-lg max-h-48 overflow-y-auto">
              {results.map(item => (
                <li
                  key={item.itemId}
                  onClick={() => selectItem(item)}
                  className="px-3 py-2 text-sm text-wow-parchment hover:bg-wow-border cursor-pointer flex items-center gap-2"
                >
                  {item.icon_url && <img src={item.icon_url} alt="" className="w-5 h-5 rounded" />}
                  {item.name}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <label className="text-xs text-wow-gray block mb-1">Time Range</label>
          <div className="flex rounded overflow-hidden border border-wow-border">
            {[7, 14, 30].map(d => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 text-sm transition-colors ${
                  days === d ? 'bg-wow-gold text-wow-brown font-semibold' : 'text-wow-gray hover:text-wow-parchment'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>
      </div>

      {selectedItem && (
        <div className="panel">
          <h2 className="panel-header">{selectedItem.name} — {days}-day price history</h2>
          {loading && <LoadingSpinner message="Loading price history..." />}
          {error && <ErrorState message={error} />}
          {trends && !loading && (
            <>
              <PriceChart data={trends} height={300} />
              {trends.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
                  <div>
                    <p className="text-wow-gray text-xs mb-1">Current Min Buyout</p>
                    <GoldDisplay copper={trends[trends.length - 1]?.min_buyout} />
                  </div>
                  <div>
                    <p className="text-wow-gray text-xs mb-1">Current Market Value</p>
                    <GoldDisplay copper={trends[trends.length - 1]?.market_value} />
                  </div>
                  <div>
                    <p className="text-wow-gray text-xs mb-1">Period Low</p>
                    <GoldDisplay copper={Math.min(...trends.map(t => t.min_buyout).filter(Boolean))} />
                  </div>
                  <div>
                    <p className="text-wow-gray text-xs mb-1">Period High</p>
                    <GoldDisplay copper={Math.max(...trends.map(t => t.market_value).filter(Boolean))} />
                  </div>
                </div>
              )}
            </>
          )}
          {trends?.length === 0 && !loading && (
            <p className="text-wow-gray text-sm text-center py-8">
              No price history yet. Data accumulates hourly once the backend is running.
            </p>
          )}
        </div>
      )}

      {!selectedItem && (
        <div className="text-center py-16 text-wow-gray">
          Search for an item to view its price trend chart.
        </div>
      )}
    </div>
  )
}
