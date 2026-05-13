import { useCallback, useState } from 'react'
import { api } from '../api/client'
import CraftingOptimizer from '../components/CraftingOptimizer/CraftingOptimizer'
import GoldDisplay from '../components/GoldDisplay'
import LoadingSpinner, { ErrorState } from '../components/LoadingSpinner'
import RealmSelector from '../components/RealmSelector'
import { useAHData } from '../hooks/useAHData'
import { useRealm } from '../hooks/useRealm'

function CraftingTable({ rows }) {
  if (!rows?.length) return <p className="text-wow-gray text-sm text-center py-8">No crafting data. Make sure recipes are seeded.</p>

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-wow-border">
            <th className="px-3 py-2 text-left text-wow-gold-dark">Item</th>
            <th className="px-3 py-2 text-left text-wow-gold-dark">Profession</th>
            <th className="px-3 py-2 text-left text-wow-gold-dark">Craft Cost</th>
            <th className="px-3 py-2 text-left text-wow-gold-dark">Market Value</th>
            <th className="px-3 py-2 text-left text-wow-gold-dark">Profit</th>
            <th className="px-3 py-2 text-left text-wow-gold-dark">ROI %</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.item_id} className="border-b border-wow-border/30 table-row-hover">
              <td className="px-3 py-2">
                <div className="flex items-center gap-2">
                  {row.icon_url && <img src={row.icon_url} alt="" className="w-6 h-6 rounded" />}
                  <span className="text-wow-parchment">{row.name}</span>
                </div>
              </td>
              <td className="px-3 py-2 text-wow-blue">{row.profession || '—'}</td>
              <td className="px-3 py-2"><GoldDisplay copper={row.crafting_cost} /></td>
              <td className="px-3 py-2"><GoldDisplay copper={row.market_value} /></td>
              <td className="px-3 py-2">
                <GoldDisplay copper={row.profit} className={row.profit > 0 ? 'text-wow-green' : 'text-wow-red'} />
              </td>
              <td className="px-3 py-2">
                <span className={row.roi > 20 ? 'text-wow-green font-semibold' : row.roi > 0 ? 'text-wow-parchment' : 'text-wow-red'}>
                  {row.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Crafting() {
  const { realm, faction } = useRealm()
  const [tab, setTab] = useState('scanner')
  const [profession, setProfession] = useState('')
  const [minRoi, setMinRoi] = useState(0)

  const fetchProfessions = useCallback(
    () => api.getProfessions().then(r => r.data),
    []
  )
  const fetchCrafting = useCallback(
    () => api.getCrafting({ realm, faction, profession: profession || undefined, min_roi: minRoi }).then(r => r.data),
    [realm, faction, profession, minRoi]
  )

  const { data: professions } = useAHData(fetchProfessions, [])
  const { data: rows, loading, error, refetch } = useAHData(fetchCrafting, [realm, faction, profession, minRoi])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-wow-gold text-2xl font-cinzel">Crafting</h1>
        <RealmSelector />
      </div>

      <div className="flex gap-2 border-b border-wow-border pb-0">
        {[['scanner', 'ROI Scanner'], ['optimizer', 'Optimizer']].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === key ? 'border-wow-gold text-wow-gold' : 'border-transparent text-wow-gray hover:text-wow-parchment'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'scanner' && (
        <div className="space-y-4">
          <div className="panel flex flex-wrap gap-3 items-end">
            <div>
              <label className="text-xs text-wow-gray block mb-1">Profession</label>
              <select value={profession} onChange={e => setProfession(e.target.value)} className="input w-40">
                <option value="">All</option>
                {professions?.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-wow-gray block mb-1">Min ROI %</label>
              <input
                type="number" min="0" step="5"
                value={minRoi}
                onChange={e => setMinRoi(Number(e.target.value))}
                className="input w-20"
              />
            </div>
          </div>

          <div className="panel">
            {loading && <LoadingSpinner message="Calculating crafting margins..." />}
            {error && <ErrorState message={error} onRetry={refetch} />}
            {rows && !loading && <CraftingTable rows={rows} />}
          </div>
        </div>
      )}

      {tab === 'optimizer' && <CraftingOptimizer />}
    </div>
  )
}
