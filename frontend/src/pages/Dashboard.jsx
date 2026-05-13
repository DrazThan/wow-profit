import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import DealScanner from '../components/DealScanner'
import GoldDisplay from '../components/GoldDisplay'
import ItemTable from '../components/ItemTable'
import LoadingSpinner, { ErrorState } from '../components/LoadingSpinner'
import RealmSelector from '../components/RealmSelector'
import { useAHData } from '../hooks/useAHData'
import { useRealm } from '../hooks/useRealm'

function StatCard({ label, value, sub }) {
  return (
    <div className="panel">
      <p className="text-wow-gray text-xs mb-1">{label}</p>
      <div className="text-wow-gold text-lg font-semibold">{value}</div>
      {sub && <p className="text-wow-gray text-xs mt-0.5">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const { realm, faction, regionId } = useRealm()
  const navigate = useNavigate()

  const fetchItems = useCallback(
    () => api.getItems({ realm, faction, region_id: regionId, limit: 10, min_sale_rate: 0.1 }).then(r => r.data),
    [realm, faction, regionId]
  )
  const fetchDeals = useCallback(
    () => api.getDeals({ realm, faction, limit: 10 }).then(r => r.data),
    [realm, faction]
  )

  const { data: items, loading: itemsLoading, error: itemsError, refetch: refetchItems } = useAHData(fetchItems, [realm, faction])
  const { data: deals, loading: dealsLoading, error: dealsError, refetch: refetchDeals } = useAHData(fetchDeals, [realm, faction])

  const topItem = items?.[0]

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h1 className="text-wow-gold text-2xl font-cinzel">Dashboard</h1>
        <RealmSelector />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Realm"
          value={`${realm} (${faction})`}
          sub="TBC Anniversary"
        />
        <StatCard
          label="Items tracked"
          value={items?.length ?? '—'}
          sub="above sale rate threshold"
        />
        {topItem && (
          <StatCard
            label="Top flip opportunity"
            value={<GoldDisplay copper={topItem.flip_profit} />}
            sub={topItem.name}
          />
        )}
        {topItem && (
          <StatCard
            label="Top margin"
            value={`${(topItem.flip_margin * 100).toFixed(1)}%`}
            sub={topItem.name}
          />
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="panel">
          <h2 className="panel-header">Top 10 Flip Opportunities</h2>
          {itemsLoading && <LoadingSpinner message="Fetching AH data..." />}
          {itemsError && <ErrorState message={itemsError} onRetry={refetchItems} />}
          {items && !itemsLoading && (
            <ItemTable items={items} onRowClick={(item) => navigate(`/items?highlight=${item.item_id}`)} />
          )}
        </div>

        <div className="panel">
          <h2 className="panel-header">Top Deals (Underpriced)</h2>
          {dealsLoading && <LoadingSpinner message="Scanning deals..." />}
          {dealsError && <ErrorState message={dealsError} onRetry={refetchDeals} />}
          {deals && !dealsLoading && <DealScanner deals={deals} />}
        </div>
      </div>
    </div>
  )
}
