import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const RealmContext = createContext(null)

export function RealmProvider({ children }) {
  const [realm, setRealm] = useState(() => localStorage.getItem('realm') || '')
  const [faction, setFaction] = useState(() => localStorage.getItem('faction') || 'horde')
  const [ready, setReady] = useState(() => !!localStorage.getItem('realm'))

  useEffect(() => {
    if (ready) return
    // No saved realm — pick the most recently uploaded one
    api.getUploadedRealms()
      .then(r => {
        const realms = r.data || []
        if (realms.length > 0) {
          const latest = realms[0]
          setRealm(latest.realm)
          setFaction(latest.faction)
          localStorage.setItem('realm', latest.realm)
          localStorage.setItem('faction', latest.faction)
        } else {
          setRealm('faerlina')
        }
      })
      .catch(() => setRealm('faerlina'))
      .finally(() => setReady(true))
  }, [ready])

  const update = (newRealm, newFaction) => {
    setRealm(newRealm)
    setFaction(newFaction)
    localStorage.setItem('realm', newRealm)
    localStorage.setItem('faction', newFaction)
  }

  return (
    <RealmContext.Provider value={{ realm, faction, update, ready }}>
      {children}
    </RealmContext.Provider>
  )
}

export function useRealm() {
  return useContext(RealmContext)
}
