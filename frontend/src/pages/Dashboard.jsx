import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import DataFreshnessPill from '../components/DataFreshnessPill'
import DealScanner from '../components/DealScanner'
import GoldDisplay from '../components/GoldDisplay'
import ItemTable from '../components/ItemTable'
import LoadingSpinner, { ErrorState } from '../components/LoadingSpinner'
import RealmSelector from '../components/RealmSelector'
import { useAHData } from '../hooks/useAHData'
import { useDataFreshness } from '../hooks/useDataFreshness'
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
  const { realm, faction } = useRealm()
  const navigate = useNavigate()
  const { freshness } = useDataFreshness(realm, faction)

  const fetchItems = useCallback(
    () => api.getItems({ realm, faction, limit: 10 }).then(r => r.data),
    [realm, faction]
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
        <div className="flex items-center gap-3">
          <h1 className="text-wow-gold text-2xl font-cinzel">Dashboard</h1>
          {freshness && (
            <DataFreshnessPill
              state={freshness.state}
              ageHours={freshness.age_hours}
              onClick={() => navigate('/upload')}
            />
          )}
        </div>
        <RealmSelector />
      </div>

      {freshness?.state === 'no_data' && (
        <div className="panel border-wow-gold/30 bg-wow-gold/5 text-sm">
          <p className="text-wow-gold font-medium">No scan data yet</p>
          <p className="text-wow-gray mt-1">
            Run a full scan with Auctionator in-game, then{' '}
            <button onClick={() => navigate('/upload')} className="text-wow-gold underline">
              upload your Auctionator.lua
            </button>{' '}
            to see prices.
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Realm"
          value={`${realm} (${faction})`}
          sub="TBC Anniversary"
        />
        <StatCard
          label="Items tracked"
          value={items?.length ?? '—'}
          sub="in latest scan"
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
          {itemsLoading && <LoadingSpinner message="Loading prices..." />}
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
