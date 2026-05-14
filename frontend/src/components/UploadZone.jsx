import { useCallback, useEffect, useRef, useState } from 'react'
import { Upload, Loader2 } from 'lucide-react'
import { api } from '../api/client'

const ACCEPTED = '.lua'
const POLL_INTERVAL = 1500

export default function UploadZone({ onSuccess }) {
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [seeding, setSeeding] = useState(null) // null | { seeding, total, seeded, pending, failed }
  const inputRef = useRef(null)
  const pollRef = useRef(null)

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const startPolling = useCallback(() => {
    stopPolling()
    pollRef.current = setInterval(async () => {
      try {
        const res = await api.getSeedStatus()
        setSeeding(res.data)
        if (!res.data.seeding) stopPolling()
      } catch {
        stopPolling()
      }
    }, POLL_INTERVAL)
  }, [])

  useEffect(() => () => stopPolling(), [])

  const doUpload = useCallback(async (file) => {
    if (!file) return
    setUploading(true)
    setResult(null)
    setError(null)
    setSeeding(null)
    stopPolling()

    const isTsm = file.name.toLowerCase().includes('appdata')

    try {
      const res = isTsm
        ? await api.uploadTsmAppdata(file)
        : await api.uploadAuctionator(file)
      setResult(res.data)
      if (res.data.seeding) {
        setSeeding(res.data.seeding)
        if (res.data.seeding.seeding) startPolling()
      }
      onSuccess?.(res.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }, [onSuccess, startPolling])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    doUpload(e.dataTransfer.files?.[0])
  }, [doUpload])

  const handleChange = useCallback((e) => {
    doUpload(e.target.files?.[0])
    e.target.value = ''
  }, [doUpload])

  const seedPct = seeding?.total > 0
    ? Math.round(((seeding.seeded + seeding.failed) / seeding.total) * 100)
    : 0

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-lg p-10 flex flex-col items-center justify-center gap-3
          cursor-pointer transition-colors duration-150 select-none
          ${dragOver ? 'border-wow-gold bg-wow-gold/5' : 'border-wow-border hover:border-wow-gold/50 hover:bg-wow-brown/40'}
          ${uploading ? 'opacity-60 cursor-not-allowed' : ''}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          className="hidden"
          onChange={handleChange}
          disabled={uploading}
        />
        <Upload size={32} className="text-wow-gold opacity-70" />
        {uploading ? (
          <p className="text-wow-parchment text-sm">Importing prices...</p>
        ) : (
          <>
            <p className="text-wow-parchment text-sm font-medium">
              Drop <code className="text-wow-gold">Auctionator.lua</code> here or click to browse
            </p>
            <p className="text-wow-gray text-xs">
              Also accepts <code>AppData.lua</code> (TSM/Kamoo format)
            </p>
          </>
        )}
      </div>

      {result && (
        <div className="panel border-green-700/40 bg-green-900/10 text-sm space-y-3">
          <p className="text-green-300 font-medium">Import successful</p>
          <p className="text-wow-parchment">
            {result.items_imported.toLocaleString()} prices imported
            {result.items_skipped > 0 && ` · ${result.items_skipped.toLocaleString()} skipped`}
          </p>
          {result.realms?.length > 0 && (
            <p className="text-wow-gray text-xs">Realms: {result.realms.join(', ')}</p>
          )}

          {seeding && (
            <SeedingProgress seeding={seeding} pct={seedPct} />
          )}
        </div>
      )}

      {error && (
        <div className="panel border-red-700/40 bg-red-900/10 text-sm">
          <p className="text-red-300 font-medium">Upload failed</p>
          <p className="text-wow-gray text-xs mt-1">{error}</p>
        </div>
      )}
    </div>
  )
}

function SeedingProgress({ seeding, pct }) {
  const done = !seeding.seeding
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        {!done && <Loader2 size={13} className="text-wow-gold animate-spin shrink-0" />}
        <p className={`text-xs font-medium ${done ? 'text-green-400' : 'text-wow-gold'}`}>
          {done
            ? `Item names loaded (${seeding.seeded.toLocaleString()} fetched)`
            : `Fetching item names… ${seeding.seeded.toLocaleString()} / ${seeding.total.toLocaleString()}`}
        </p>
      </div>
      {!done && (
        <div className="w-full bg-wow-brown rounded-full h-1.5 overflow-hidden">
          <div
            className="bg-wow-gold h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
      {done && seeding.failed > 0 && (
        <p className="text-wow-gray text-xs">
          {seeding.failed.toLocaleString()} items had no Wowhead data
        </p>
      )}
    </div>
  )
}
