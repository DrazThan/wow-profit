import { createContext, useContext, useState } from 'react'

const RealmContext = createContext(null)

export function RealmProvider({ children }) {
  const [realm, setRealm] = useState(
    () => localStorage.getItem('realm') || 'faerlina'
  )
  const [faction, setFaction] = useState(
    () => localStorage.getItem('faction') || 'horde'
  )
  const [regionId] = useState(1)

  const update = (newRealm, newFaction) => {
    setRealm(newRealm)
    setFaction(newFaction)
    localStorage.setItem('realm', newRealm)
    localStorage.setItem('faction', newFaction)
  }

  return (
    <RealmContext.Provider value={{ realm, faction, regionId, update }}>
      {children}
    </RealmContext.Provider>
  )
}

export function useRealm() {
  return useContext(RealmContext)
}
