import { useCallback, useEffect, useRef, useState } from 'react'

export function useAHData(fetcher, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const load = useCallback(async () => {
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)
    setError(null)
    try {
      const result = await fetcher(controller.signal)
      if (!controller.signal.aborted) {
        setData(result)
        setError(null)
      }
    } catch (e) {
      if (!controller.signal.aborted) {
        setError(e.message || 'Failed to load')
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false)
      }
    }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    load()
    return () => abortRef.current?.abort()
  }, [load])

  return { data, loading, error, refetch: load }
}
