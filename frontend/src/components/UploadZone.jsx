import { useCallback, useRef, useState } from 'react'
import { Upload } from 'lucide-react'
import { api } from '../api/client'

const ACCEPTED = '.lua'

export default function UploadZone({ onSuccess }) {
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const doUpload = useCallback(async (file) => {
    if (!file) return
    setUploading(true)
    setResult(null)
    setError(null)

    const isAuctionator = file.name.toLowerCase().includes('auctionator')
    const isTsm = file.name.toLowerCase().includes('appdata')

    try {
      let res
      if (isTsm) {
        res = await api.uploadTsmAppdata(file)
      } else {
        res = await api.uploadAuctionator(file)
      }
      setResult(res.data)
      onSuccess?.(res.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }, [onSuccess])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    doUpload(file)
  }, [doUpload])

  const handleChange = useCallback((e) => {
    doUpload(e.target.files?.[0])
    e.target.value = ''
  }, [doUpload])

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
          ${dragOver
            ? 'border-wow-gold bg-wow-gold/5'
            : 'border-wow-border hover:border-wow-gold/50 hover:bg-wow-brown/40'}
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
        <div className="panel border-green-700/40 bg-green-900/10 text-sm space-y-1">
          <p className="text-green-300 font-medium">Import successful</p>
          <p className="text-wow-parchment">
            {result.items_imported.toLocaleString()} items imported
            {result.items_skipped > 0 && ` · ${result.items_skipped.toLocaleString()} skipped`}
          </p>
          {result.realms?.length > 0 && (
            <p className="text-wow-gray text-xs">Realms: {result.realms.join(', ')}</p>
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
