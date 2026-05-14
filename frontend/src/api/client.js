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
  // Upload
  uploadAuctionator: (file) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/upload/auctionator', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  uploadTsmAppdata: (file) => {
    const form = new FormData()
    form.append('file', file)
    return client.post('/upload/tsm-appdata', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  getUploadStatus: (params) => client.get('/upload/status', { params }),
  getUploadHistory: (params) => client.get('/upload/history', { params }),
  getUploadedRealms: () => client.get('/upload/realms'),
  getSeedStatus: () => client.get('/upload/seed-status'),

  // Realms
  getRealms: () => client.get('/realms'),

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
