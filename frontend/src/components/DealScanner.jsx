import GoldDisplay from './GoldDisplay'

const QUALITY_COLORS = { 1: 'text-wow-common', 2: 'text-wow-green', 3: 'text-wow-blue', 4: 'text-wow-purple', 5: 'text-wow-orange' }

export default function DealScanner({ deals = [], onItemClick }) {
  if (!deals.length) {
    return <p className="text-wow-gray text-sm py-4 text-center">No deals found for this realm/faction.</p>
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-wow-border">
            <th className="px-3 py-2 text-left text-wow-gold-dark">Item</th>
            <th className="px-3 py-2 text-left text-wow-gold-dark">Min Buyout</th>
            <th className="px-3 py-2 text-left text-wow-gold-dark">Market Value</th>
            <th className="px-3 py-2 text-left text-wow-gold-dark">Discount</th>
            <th className="px-3 py-2 text-left text-wow-gold-dark">Qty</th>
          </tr>
        </thead>
        <tbody>
          {deals.map((deal, i) => {
            const discount = deal.marketValue > 0
              ? ((deal.marketValue - deal.minBuyout) / deal.marketValue * 100).toFixed(0)
              : 0
            return (
              <tr
                key={deal.itemId ?? i}
                onClick={() => onItemClick?.(deal)}
                className="border-b border-wow-border/30 table-row-hover cursor-pointer"
              >
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2">
                    {deal.icon_url && <img src={deal.icon_url} alt="" className="w-6 h-6 rounded" />}
                    <span className={QUALITY_COLORS[deal.quality] || 'text-wow-parchment'}>
                      {deal.name || `Item #${deal.itemId}`}
                    </span>
                  </div>
                </td>
                <td className="px-3 py-2"><GoldDisplay copper={deal.minBuyout} /></td>
                <td className="px-3 py-2"><GoldDisplay copper={deal.marketValue} /></td>
                <td className="px-3 py-2">
                  <span className={Number(discount) >= 30 ? 'text-wow-green font-semibold' : 'text-wow-gold'}>
                    -{discount}%
                  </span>
                </td>
                <td className="px-3 py-2 text-wow-gray">{deal.quantity ?? '—'}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
