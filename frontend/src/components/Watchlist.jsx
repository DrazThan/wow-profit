import { Trash2 } from 'lucide-react'
import GoldDisplay from './GoldDisplay'

export default function Watchlist({ items = [], onRemove, onItemClick }) {
  if (!items.length) {
    return (
      <p className="text-wow-gray text-sm py-4 text-center">
        No items on watchlist. Search for items and pin them.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.id}
          className={`panel flex items-center gap-3 cursor-pointer ${
            item.alert === 'below' ? 'border-wow-green' : item.alert === 'above' ? 'border-wow-orange' : ''
          }`}
          onClick={() => onItemClick?.(item)}
        >
          {item.icon_url && <img src={item.icon_url} alt="" className="w-8 h-8 rounded shrink-0" />}
          <div className="flex-1 min-w-0">
            <p className="text-wow-parchment font-medium truncate">{item.name}</p>
            <div className="flex gap-4 text-xs mt-0.5">
              <span className="text-wow-gray">
                Buyout: <GoldDisplay copper={item.min_buyout} />
              </span>
              <span className="text-wow-gray">
                MV: <GoldDisplay copper={item.market_value} />
              </span>
              {item.flip_profit > 0 && (
                <span className="text-wow-green">
                  +<GoldDisplay copper={item.flip_profit} />
                </span>
              )}
            </div>
            {item.alert && (
              <p className={`text-xs mt-0.5 ${item.alert === 'below' ? 'text-wow-green' : 'text-wow-orange'}`}>
                ⚠ Price {item.alert === 'below' ? 'dropped below alert' : 'rose above alert'}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {item.alert_below && (
              <span className="text-xs text-wow-gray">Alert ↓ <GoldDisplay copper={item.alert_below} /></span>
            )}
            <button
              onClick={(e) => { e.stopPropagation(); onRemove?.(item.id) }}
              className="text-wow-gray hover:text-wow-red transition-colors p-1"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
