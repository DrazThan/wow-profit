import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { BarChart2, BookOpen, Eye, Home, Sword, TrendingUp } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Items from './pages/Items'
import Crafting from './pages/Crafting'
import Trends from './pages/Trends'
import WatchlistPage from './pages/WatchlistPage'
import { RealmProvider } from './hooks/useRealm'

const NAV = [
  { to: '/', icon: Home, label: 'Dashboard' },
  { to: '/items', icon: BarChart2, label: 'Items' },
  { to: '/crafting', icon: Sword, label: 'Crafting' },
  { to: '/trends', icon: TrendingUp, label: 'Trends' },
  { to: '/watchlist', icon: Eye, label: 'Watchlist' },
]

function Sidebar() {
  return (
    <aside className="w-52 min-h-screen bg-wow-brown border-r border-wow-border flex flex-col shrink-0">
      <div className="p-4 border-b border-wow-border">
        <h1 className="font-cinzel text-wow-gold text-xl font-bold leading-tight">
          AH Profit
        </h1>
        <p className="text-wow-gray text-xs mt-0.5">TBC Classic Tracker</p>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors duration-100 ${
                isActive
                  ? 'bg-wow-border text-wow-gold font-medium'
                  : 'text-wow-parchment hover:bg-wow-border/50 hover:text-wow-gold'
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-wow-border text-xs text-wow-gray">
        <p>Data: TSM + NexusHub</p>
        <p className="mt-0.5 text-wow-border">TBC Anniversary</p>
      </div>
    </aside>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <RealmProvider>
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/items" element={<Items />} />
              <Route path="/crafting" element={<Crafting />} />
              <Route path="/trends" element={<Trends />} />
              <Route path="/watchlist" element={<WatchlistPage />} />
            </Routes>
          </main>
        </div>
      </RealmProvider>
    </BrowserRouter>
  )
}
