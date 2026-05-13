import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import GoldDisplay from '../GoldDisplay'
import BuyCraftToggle from './BuyCraftToggle'

const MODE_BORDER = {
  craft: 'border-l-2 border-l-wow-green',
  forced_craft: 'border-l-2 border-l-yellow-400',
  buy: 'border-l-2 border-l-transparent',
  forced_buy: 'border-l-2 border-l-yellow-400',
  buy_only: 'border-l-2 border-l-transparent',
}

export default function CraftingTreeNode({ node, overrides, onSetOverride, depth = 0 }) {
  const [expanded, setExpanded] = useState(depth < 2)
  const hasCraft = node.craft_cost_each != null
  const isForced = node.mode.startsWith('forced_')
  const isCrafting = node.mode === 'craft' || node.mode === 'forced_craft'
  const worseThanBuy = isCrafting && node.craft_cost_each > node.ah_price_each && node.ah_price_each > 0

  return (
    <div className={`${depth > 0 ? 'ml-4 mt-1' : ''}`}>
      <div
        className={`${MODE_BORDER[node.mode] || ''} bg-wow-brown-light rounded-r px-3 py-2 flex items-start gap-2 group`}
      >
        {hasCraft && node.recipe_mats?.length > 0 && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="mt-0.5 text-wow-gray hover:text-wow-gold shrink-0"
          >
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        )}
        {(!hasCraft || !node.recipe_mats?.length) && <span className="w-3.5 shrink-0" />}

        {node.icon_url && (
          <img src={node.icon_url} alt="" className="w-6 h-6 rounded shrink-0 mt-0.5" />
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-wow-parchment font-medium">
              {node.quantity_needed}× {node.name}
            </span>
            {isForced && (
              <span className="text-xs text-yellow-400 border border-yellow-400/50 rounded px-1">override</span>
            )}
            {worseThanBuy && (
              <span className="text-xs text-wow-red">
                +<GoldDisplay copper={(node.craft_cost_each - node.ah_price_each) * node.quantity_needed} /> more than buying
              </span>
            )}
          </div>

          <div className="flex items-center gap-4 mt-0.5 text-xs text-wow-gray flex-wrap">
            <span>AH: <GoldDisplay copper={node.ah_price_each} /></span>
            {hasCraft && (
              <span className={node.craft_cost_each < node.ah_price_each ? 'text-wow-green' : 'text-wow-gray'}>
                Craft: <GoldDisplay copper={node.craft_cost_each} />
              </span>
            )}
            <span className="text-wow-parchment">
              Total: <GoldDisplay copper={node.total_cost} />
            </span>
            {node.savings_vs_buy > 0 && (
              <span className="text-wow-green">saves <GoldDisplay copper={node.savings_vs_buy} /></span>
            )}
            {node.profession && (
              <span className="text-wow-blue">{node.profession}</span>
            )}
          </div>
        </div>

        <div className="shrink-0">
          <BuyCraftToggle
            mode={node.mode}
            hasCraft={hasCraft}
            onSet={(m) => onSetOverride(node.item_id, m)}
          />
        </div>
      </div>

      {expanded && isCrafting && node.recipe_mats?.length > 0 && (
        <div className="border-l border-wow-border ml-3 pl-1 mt-1 space-y-1">
          {node.recipe_mats.map((mat) => (
            <CraftingTreeNode
              key={mat.item_id}
              node={mat}
              overrides={overrides}
              onSetOverride={onSetOverride}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
