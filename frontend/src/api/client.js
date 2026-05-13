import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Unknown error'
    return Promise.reject(new Error(msg))
  }
)

export const api = {
  // Realms
  getRegions: () => client.get('/realms/regions'),
  getRealms: (regionId) => client.get('/realms', { params: { region_id: regionId } }),

  // Items
  getItems: (params) => client.get('/items', { params }),
  searchItems: (q) => client.get('/items/search', { params: { q } }),
  getItem: (itemId, params) => client.get(`/items/${itemId}`, { params }),

  // Deals
  getDeals: (params) => client.get('/deals', { params }),

  // Trends
  getTrends: (itemId, params) => client.get(`/trends/${itemId}`, { params }),

  // Crafting
  getCrafting: (params) => client.get('/crafting', { params }),
  getProfessions: () => client.get('/crafting/professions'),
  optimizeCrafting: (body) => client.post('/crafting/optimize', body),

  // Watchlist
  getWatchlist: (params) => client.get('/watchlist', { params }),
  addToWatchlist: (body) => client.post('/watchlist', body),
  removeFromWatchlist: (id) => client.delete(`/watchlist/${id}`),
}

export default client
