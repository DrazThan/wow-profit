import { useCallback, useState } from 'react'
import { api } from '../api/client'
import GoldDisplay from '../components/GoldDisplay'
import ItemTable from '../components/ItemTable'
import LoadingSpinner, { ErrorState } from '../components/LoadingSpinner'
import PriceChart from '../components/PriceChart'
import RealmSelector from '../components/RealmSelector'
import { useAHData } from '../hooks/useAHData'
import { useRealm } from '../hooks/useRealm'

function FilterBar({ filters, onChange }) {
  return (
    <div className="flex flex-wrap gap-3 items-end">
      <div>
        <label className="text-xs text-wow-gray block mb-1">Min Margin %</label>
        <input
          type="number" min="0" max="100" step="5"
          value={Math.round(filters.min_margin * 100)}
          onChange={e => onChange({ ...filters, min_margin: Number(e.target.value) / 100 })}
          className="input w-20"
        />
      </div>
      <div>
        <label className="text-xs text-wow-gray block mb-1">Sort By</label>
        <select
          value={filters.sort_by}
          onChange={e => onChange({ ...filters, sort_by: e.target.value })}
          className="input w-36"
        >
          <option value="flip_profit">Flip Profit</option>
          <option value="flip_margin">Margin %</option>
        </select>
      </div>
      <p className="text-xs text-wow-gray self-end pb-1">
        Sale rate &amp; daily vol. available on item detail (region endpoint)
      </p>
    </div>
  )
}

function ItemDetailPanel({ item, realm, faction, onClose }) {
  const fetchDetail = useCallback(
    () => api.getItem(item.item_id, { realm, faction }).then(r => r.data),
    [item.item_id, realm, faction]
  )
  const fetchTrends = useCallback(
    () => api.getTrends(item.item_id, { realm, faction, days: 14 }).then(r => r.data),
    [item.item_id, realm, faction]
  )
  const { data: detail } = useAHData(fetchDetail, [item.item_id])
  const { data: trends } = useAHData(fetchTrends, [item.item_id])

  return (
    <div className="panel border-wow-gold/40 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-wow-gold font-cinzel">{item.name}</h3>
        <button onClick={onClose} className="text-wow-gray hover:text-wow-parchment text-lg leading-none">×</button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <div><p className="text-wow-gray text-xs">Min Buyout</p><GoldDisplay copper={item.min_buyout} /></div>
        <div><p className="text-wow-gray text-xs">Market Value</p><GoldDisplay copper={item.market_value} /></div>
        <div><p className="text-wow-gray text-xs">Flip Profit (after 5% cut)</p><GoldDisplay copper={item.flip_profit} className="text-wow-green" /></div>
        <div><p className="text-wow-gray text-xs">Margin</p><span className="text-wow-green">{(item.flip_margin * 100).toFixed(1)}%</span></div>
        <div><p className="text-wow-gray text-xs">Sale Rate</p><span>{item.sale_pct > 0 ? `${item.sale_pct}%` : '—'}</span></div>
        <div><p className="text-wow-gray text-xs">Daily Sold</p><span>{item.sold_per_day > 0 ? item.sold_per_day.toFixed(1) : '—'}</span></div>
        <div><p className="text-wow-gray text-xs">Auctions</p><span>{item.num_auctions}</span></div>
        {item.vendor_sell > 0 && <div><p className="text-wow-gray text-xs">Vendor Sell</p><GoldDisplay copper={item.vendor_sell} /></div>}
      </div>

      {detail?.crafting_cost && (
        <div className="flex gap-4 text-sm">
          <div><p className="text-wow-gray text-xs">Craft Cost</p><GoldDisplay copper={detail.crafting_cost} /></div>
          <div><p className="text-wow-gray text-xs">Craft Profit</p><GoldDisplay copper={detail.crafting_profit} className="text-wow-green" /></div>
          <div><p className="text-wow-gray text-xs">Craft ROI</p><span className="text-wow-green">{detail.crafting_roi?.toFixed(1)}%</span></div>
        </div>
      )}

      {trends?.length > 0 && (
        <div>
          <p className="text-xs text-wow-gray mb-2">14-day price history</p>
          <PriceChart data={trends} height={180} />
        </div>
      )}
    </div>
  )
}

const DEFAULT_FILTERS = { min_margin: 0, sort_by: 'flip_profit', limit: 100 }

export default function Items() {
  const { realm, faction } = useRealm()
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [selected, setSelected] = useState(null)

  const fetchItems = useCallback(
    () => api.getItems({ ...filters, realm, faction }).then(r => r.data),
    [realm, faction, filters]
  )
  const { data: items, loading, error, refetch } = useAHData(fetchItems, [realm, faction, filters])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-wow-gold text-2xl font-cinzel">Item Scanner</h1>
        <RealmSelector />
      </div>

      <div className="panel space-y-3">
        <FilterBar filters={filters} onChange={setFilters} />
      </div>

      {selected && (
        <ItemDetailPanel
          item={selected}
          realm={realm}
          faction={faction}
          onClose={() => setSelected(null)}
        />
      )}

      <div className="panel">
        {loading && <LoadingSpinner message="Scanning auction house..." />}
        {error && <ErrorState message={error} onRetry={refetch} />}
        {items && !loading && (
          <>
            <div className="flex justify-between items-center mb-3">
              <span className="text-wow-gray text-sm">{items.length} items found</span>
            </div>
            <ItemTable items={items} onRowClick={setSelected} />
          </>
        )}
      </div>
    </div>
  )
}
