import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'

const LS_KEY = 'crafting_overrides'

function loadOverrides() {
  try { return JSON.parse(localStorage.getItem(LS_KEY) || '{}') } catch { return {} }
}

export function useCraftingTree(realm, faction) {
  const [itemId, setItemId] = useState(null)
  const [quantity, setQuantity] = useState(1)
  const [tree, setTree] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [overrides, setOverrides] = useState(loadOverrides)

  const fetchTree = useCallback(async (id, qty, ovr) => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.optimizeCrafting({ item_id: id, quantity: qty, realm, faction, overrides: ovr })
      setTree(res.data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [realm, faction])

  useEffect(() => {
    if (itemId) fetchTree(itemId, quantity, overrides)
  }, [itemId, quantity, realm, faction]) // eslint-disable-line react-hooks/exhaustive-deps

  const setOverride = useCallback((nodeItemId, mode) => {
    setOverrides(prev => {
      const next = mode === 'auto'
        ? Object.fromEntries(Object.entries(prev).filter(([k]) => k !== String(nodeItemId)))
        : { ...prev, [String(nodeItemId)]: mode }
      localStorage.setItem(LS_KEY, JSON.stringify(next))
      fetchTree(itemId, quantity, next)
      return next
    })
  }, [itemId, quantity, fetchTree])

  const clearOverrides = useCallback(() => {
    setOverrides({})
    localStorage.removeItem(LS_KEY)
    if (itemId) fetchTree(itemId, quantity, {})
  }, [itemId, quantity, fetchTree])

  return { itemId, setItemId, quantity, setQuantity, tree, loading, error, overrides, setOverride, clearOverrides }
}
