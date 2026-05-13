export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-8 h-8 border-2 border-wow-border border-t-wow-gold rounded-full animate-spin" />
      <p className="text-wow-gray text-sm">{message}</p>
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <p className="text-wow-red">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-outline">
          Retry
        </button>
      )}
    </div>
  )
}
