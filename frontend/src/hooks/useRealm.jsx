import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const RealmContext = createContext(null)

export function RealmProvider({ children }) {
  const [realm, setRealm] = useState(() => localStorage.getItem('realm') || 'faerlina')
  const [faction, setFaction] = useState(() => localStorage.getItem('faction') || 'horde')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    // Always fetch uploaded realms on mount. If the saved realm isn't one we
    // have data for, switch to the most recently uploaded one automatically.
    api.getUploadedRealms()
      .then(r => {
        const realms = r.data || []
        const savedRealm = localStorage.getItem('realm')
        const savedInList = realms.some(r => r.realm === savedRealm)
        if (!savedRealm || !savedInList) {
          if (realms.length > 0) {
            const latest = realms[0]
            setRealm(latest.realm)
            setFaction(latest.faction)
            localStorage.setItem('realm', latest.realm)
            localStorage.setItem('faction', latest.faction)
          }
        }
      })
      .catch(() => {})
      .finally(() => setReady(true))
  }, [])

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
