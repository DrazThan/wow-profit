import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

function formatCopper(copper) {
  if (!copper) return '0c'
  const g = Math.floor(copper / 10000)
  const s = Math.floor((copper % 10000) / 100)
  if (g) return `${g}g ${s}s`
  return `${s}s`
}

function formatDate(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-wow-brown border border-wow-border rounded p-2 text-xs">
      <p className="text-wow-gold mb-1">{formatDate(label)}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {formatCopper(p.value)}
        </p>
      ))}
    </div>
  )
}

export default function PriceChart({ data = [], height = 220 }) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center text-wow-gray text-sm" style={{ height }}>
        No price history available
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#3d2610" />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatDate}
          tick={{ fill: '#8b8b8b', fontSize: 11 }}
          axisLine={{ stroke: '#5a3e1b' }}
        />
        <YAxis
          tickFormatter={formatCopper}
          tick={{ fill: '#8b8b8b', fontSize: 11 }}
          axisLine={{ stroke: '#5a3e1b' }}
          width={60}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12, color: '#f5e6c8' }} />
        <Line
          type="monotone"
          dataKey="min_buyout"
          name="Min Buyout"
          stroke="#ff8000"
          dot={false}
          strokeWidth={2}
        />
        <Line
          type="monotone"
          dataKey="market_value"
          name="Market Value"
          stroke="#ffd100"
          dot={false}
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
