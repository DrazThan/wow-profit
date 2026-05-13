import { useCallback, useState } from 'react'
import { api } from '../api/client'
import ItemTable from '../components/ItemTable'
import LoadingSpinner, { ErrorState } from '../components/LoadingSpinner'
import RealmSelector from '../components/RealmSelector'
import Watchlist from '../components/Watchlist'
import { useAHData } from '../hooks/useAHData'
import { useItemSearch } from '../hooks/useItemSearch'
import { useRealm } from '../hooks/useRealm'

export default function WatchlistPage() {
  const { realm, faction, regionId } = useRealm()
  const [showSearch, setShowSearch] = useState(false)
  const [alertBelow, setAlertBelow] = useState('')
  const [alertAbove, setAlertAbove] = useState('')
  const [addingItem, setAddingItem] = useState(null)
  const { query, setQuery, results } = useItemSearch()

  const fetchWatchlist = useCallback(
    () => api.getWatchlist({ realm, faction, region_id: regionId }).then(r => r.data),
    [realm, faction, regionId]
  )
  const { data: items, loading, error, refetch } = useAHData(fetchWatchlist, [realm, faction])

  const addItem = async (item) => {
    setAddingItem(item)
    setShowSearch(false)
    setQuery('')
  }

  const confirmAdd = async () => {
    if (!addingItem) return
    try {
      await api.addToWatchlist({
        item_id: addingItem.itemId || addingItem.item_id,
        realm,
        faction,
        alert_below: alertBelow ? Number(alertBelow) * 10000 : null,
        alert_above: alertAbove ? Number(alertAbove) * 10000 : null,
      })
      setAddingItem(null)
      setAlertBelow('')
      setAlertAbove('')
      refetch()
    } catch (e) {
      alert(e.message)
    }
  }

  const removeItem = async (id) => {
    await api.removeFromWatchlist(id)
    refetch()
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-wow-gold text-2xl font-cinzel">Watchlist</h1>
        <RealmSelector />
      </div>

      <div className="panel space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-wow-gold font-medium">Add Item</h2>
          <button onClick={() => setShowSearch(s => !s)} className="btn-outline text-xs">
            {showSearch ? 'Cancel' : '+ Add item'}
          </button>
        </div>

        {showSearch && (
          <div className="space-y-2">
            <div className="relative">
              <input
                className="input"
                placeholder="Search for item..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                autoFocus
              />
              {results.length > 0 && (
                <ul className="absolute z-20 top-full left-0 right-0 mt-1 bg-wow-brown border border-wow-border rounded max-h-48 overflow-y-auto">
                  {results.map(item => (
                    <li
                      key={item.itemId}
                      onClick={() => addItem(item)}
                      className="px-3 py-2 text-sm text-wow-parchment hover:bg-wow-border cursor-pointer flex items-center gap-2"
                    >
                      {item.icon_url && <img src={item.icon_url} alt="" className="w-5 h-5 rounded" />}
                      {item.name}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}

        {addingItem && (
          <div className="panel border-wow-gold/40 space-y-3">
            <p className="text-wow-parchment">
              Adding <span className="text-wow-gold">{addingItem.name}</span> to watchlist
            </p>
            <div className="flex gap-3 flex-wrap">
              <div>
                <label className="text-xs text-wow-gray block mb-1">Alert below (gold)</label>
                <input
                  type="number" min="0" step="1"
                  placeholder="e.g. 10"
                  value={alertBelow}
                  onChange={e => setAlertBelow(e.target.value)}
                  className="input w-28"
                />
              </div>
              <div>
                <label className="text-xs text-wow-gray block mb-1">Alert above (gold)</label>
                <input
                  type="number" min="0" step="1"
                  placeholder="e.g. 50"
                  value={alertAbove}
                  onChange={e => setAlertAbove(e.target.value)}
                  className="input w-28"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={confirmAdd} className="btn-gold">Add to Watchlist</button>
              <button onClick={() => setAddingItem(null)} className="btn-outline">Cancel</button>
            </div>
          </div>
        )}
      </div>

      <div className="panel">
        <h2 className="panel-header">Tracked Items</h2>
        {loading && <LoadingSpinner message="Loading watchlist..." />}
        {error && <ErrorState message={error} onRetry={refetch} />}
        {items && !loading && (
          <Watchlist items={items} onRemove={removeItem} />
        )}
      </div>
    </div>
  )
}
