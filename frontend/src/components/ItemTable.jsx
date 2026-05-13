import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import GoldDisplay from './GoldDisplay'

const QUALITY_COLORS = {
  1: 'text-wow-common',
  2: 'text-wow-green',
  3: 'text-wow-blue',
  4: 'text-wow-purple',
  5: 'text-wow-orange',
}

const COLS = [
  { key: 'name', label: 'Item' },
  { key: 'min_buyout', label: 'Min Buyout' },
  { key: 'market_value', label: 'Market Value' },
  { key: 'flip_profit', label: 'Flip Profit' },
  { key: 'flip_margin', label: 'Margin %' },
  { key: 'region_sale_rate', label: 'Sale Rate' },
  { key: 'region_avg_daily_sold', label: 'Daily Vol.' },
  { key: 'num_auctions', label: 'Auctions' },
]

export default function ItemTable({ items = [], onRowClick }) {
  const [sortKey, setSortKey] = useState('flip_profit')
  const [sortDir, setSortDir] = useState('desc')

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const sorted = [...items].sort((a, b) => {
    const av = a[sortKey] ?? 0
    const bv = b[sortKey] ?? 0
    if (sortKey === 'name') return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    return sortDir === 'asc' ? av - bv : bv - av
  })

  if (!items.length) {
    return (
      <div className="text-center py-12 text-wow-gray">
        No items found. Try adjusting filters.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-wow-border">
            {COLS.map(({ key, label }) => (
              <th
                key={key}
                onClick={() => handleSort(key)}
                className="px-3 py-2 text-left text-wow-gold-dark cursor-pointer hover:text-wow-gold select-none whitespace-nowrap"
              >
                <span className="inline-flex items-center gap-1">
                  {label}
                  {sortKey === key && (
                    sortDir === 'desc' ? <ChevronDown size={12} /> : <ChevronUp size={12} />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((item) => (
            <tr
              key={item.item_id}
              onClick={() => onRowClick?.(item)}
              className="border-b border-wow-border/30 table-row-hover cursor-pointer"
            >
              <td className="px-3 py-2">
                <div className="flex items-center gap-2">
                  {item.icon_url && (
                    <img src={item.icon_url} alt="" className="w-6 h-6 rounded" />
                  )}
                  <span className={QUALITY_COLORS[item.quality] || 'text-wow-parchment'}>
                    {item.name}
                  </span>
                </div>
              </td>
              <td className="px-3 py-2"><GoldDisplay copper={item.min_buyout} /></td>
              <td className="px-3 py-2"><GoldDisplay copper={item.market_value} /></td>
              <td className="px-3 py-2">
                <GoldDisplay
                  copper={item.flip_profit}
                  className={item.flip_profit > 0 ? 'text-wow-green' : 'text-wow-red'}
                />
              </td>
              <td className="px-3 py-2">
                <span className={item.flip_margin > 0.15 ? 'text-wow-green' : item.flip_margin > 0 ? 'text-wow-parchment' : 'text-wow-red'}>
                  {(item.flip_margin * 100).toFixed(1)}%
                </span>
              </td>
              <td className="px-3 py-2">
                <span className={item.region_sale_rate > 0.5 ? 'text-wow-green' : item.region_sale_rate > 0.2 ? 'text-wow-gold' : 'text-wow-red'}>
                  {(item.region_sale_rate * 100).toFixed(0)}%
                </span>
              </td>
              <td className="px-3 py-2 text-wow-gray">
                {item.region_avg_daily_sold?.toFixed(1) ?? '—'}
              </td>
              <td className="px-3 py-2 text-wow-gray">{item.num_auctions ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
