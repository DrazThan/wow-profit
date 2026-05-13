import { useEffect, useState } from 'react'
import { api } from '../api/client'

export function useDataFreshness(realm, faction) {
  const [freshness, setFreshness] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!realm || !faction) return
    setLoading(true)
    api.getUploadStatus({ realm, faction })
      .then(r => setFreshness(r.data))
      .catch(() => setFreshness({ state: 'no_data' }))
      .finally(() => setLoading(false))
  }, [realm, faction])

  return { freshness, loading }
}
