import GoldDisplay from '../GoldDisplay'

function allBuyCost(node) {
  if (!node) return 0
  return node.ah_price_each * node.quantity_needed
}

function totalSavings(node) {
  if (!node) return 0
  return node.savings_vs_buy + (node.recipe_mats?.reduce((s, m) => s + totalSavings(m), 0) ?? 0)
}

export default function CostSummaryBar({ tree }) {
  if (!tree) return null

  const optimized = tree.total_cost
  const allBuy = allBuyCost(tree)
  const savings = allBuy - optimized

  return (
    <div className="panel border-wow-gold/50 grid grid-cols-3 gap-4 text-center">
      <div>
        <p className="text-wow-gray text-xs mb-1">All-buy cost</p>
        <GoldDisplay copper={allBuy} className="text-base" />
      </div>
      <div>
        <p className="text-wow-gray text-xs mb-1">Optimized cost</p>
        <GoldDisplay copper={optimized} className="text-base text-wow-gold" />
      </div>
      <div>
        <p className="text-wow-gray text-xs mb-1">You save</p>
        <div>
          <GoldDisplay copper={savings} className={`text-base ${savings > 0 ? 'text-wow-green' : 'text-wow-gray'}`} />
          {allBuy > 0 && savings > 0 && (
            <span className="text-wow-green text-xs ml-1">
              ({((savings / allBuy) * 100).toFixed(0)}%)
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
