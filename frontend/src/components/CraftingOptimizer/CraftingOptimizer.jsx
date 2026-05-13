import { useState } from 'react'
import { RefreshCw, X } from 'lucide-react'
import { useRealm } from '../../hooks/useRealm'
import { useItemSearch } from '../../hooks/useItemSearch'
import LoadingSpinner, { ErrorState } from '../LoadingSpinner'
import CostSummaryBar from './CostSummaryBar'
import CraftingTreeNode from './CraftingTreeNode'
import { useCraftingTree } from './useCraftingTree'

export default function CraftingOptimizer() {
  const { realm, faction } = useRealm()
  const { itemId, setItemId, quantity, setQuantity, tree, loading, error, overrides, setOverride, clearOverrides } =
    useCraftingTree(realm, faction)
  const { query, setQuery, results, loading: searching } = useItemSearch()
  const [showSearch, setShowSearch] = useState(!itemId)

  const selectItem = (item) => {
    setItemId(item.itemId || item.item_id)
    setQuery('')
    setShowSearch(false)
  }

  return (
    <div className="space-y-4">
      {/* Item picker */}
      <div className="panel">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 min-w-48">
            <input
              className="input"
              placeholder="Search item to craft..."
              value={query}
              onChange={(e) => { setQuery(e.target.value); setShowSearch(true) }}
              onFocus={() => setShowSearch(true)}
            />
            {showSearch && results.length > 0 && (
              <ul className="absolute z-20 top-full left-0 right-0 mt-1 bg-wow-brown border border-wow-border rounded shadow-lg max-h-48 overflow-y-auto">
                {results.map((item) => (
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

          <div className="flex items-center gap-2">
            <label className="text-xs text-wow-gray">Qty</label>
            <input
              type="number"
              min="1"
              max="200"
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
              className="input w-16 text-center"
            />
          </div>

          {Object.keys(overrides).length > 0 && (
            <button onClick={clearOverrides} className="btn-outline flex items-center gap-1 text-xs">
              <X size={12} /> Clear overrides
            </button>
          )}
        </div>
      </div>

      {loading && <LoadingSpinner message="Resolving crafting tree..." />}
      {error && <ErrorState message={error} />}

      {tree && !loading && (
        <>
          <CostSummaryBar tree={tree} />
          <div className="panel space-y-1">
            <CraftingTreeNode
              node={tree}
              overrides={overrides}
              onSetOverride={setOverride}
              depth={0}
            />
          </div>
        </>
      )}

      {!tree && !loading && !error && (
        <div className="text-center py-12 text-wow-gray">
          Search for a craftable item to see the optimized cost breakdown.
        </div>
      )}
    </div>
  )
}
