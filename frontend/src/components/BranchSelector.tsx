import { useState, useEffect } from 'react'

interface BranchSelectorProps {
  projectId: string
  currentBranch: string | null
  onBranchChange: (branch: string) => void
  onSync: () => void
  disabled?: boolean
}

export default function BranchSelector({ 
  projectId, 
  currentBranch, 
  onBranchChange, 
  onSync, 
  disabled = false 
}: BranchSelectorProps) {
  const [branches, setBranches] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [syncLoading, setSyncLoading] = useState(false)

  useEffect(() => {
    loadBranches()
  }, [projectId])

  const loadBranches = async () => {
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:5000/api/db/projects/${projectId}/branches`)
      const data = await response.json()
      
      if (response.ok) {
        setBranches(data.branches || [])
      } else {
        console.error('Failed to load branches:', data.error)
      }
    } catch (err) {
      console.error('Error loading branches:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleBranchChange = async (newBranch: string) => {
    if (newBranch === currentBranch) return
    
    try {
      setLoading(true)
      const response = await fetch(`http://localhost:5000/api/db/projects/${projectId}/switch-branch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ branch: newBranch })
      })
      
      if (response.ok) {
        onBranchChange(newBranch)
      } else {
        const data = await response.json()
        alert(`Failed to switch branch: ${data.error}`)
      }
    } catch (err) {
      console.error('Error switching branch:', err)
      alert('Failed to switch branch')
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async () => {
    try {
      setSyncLoading(true)
      const response = await fetch(`http://localhost:5000/api/db/projects/${projectId}/sync`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const data = await response.json()
        alert(data.message || 'Project synced successfully')
        onSync()
      } else {
        const data = await response.json()
        alert(`Failed to sync: ${data.error}`)
      }
    } catch (err) {
      console.error('Error syncing project:', err)
      alert('Failed to sync project')
    } finally {
      setSyncLoading(false)
    }
  }

  if (branches.length === 0) {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={handleSync}
          disabled={disabled || syncLoading}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {syncLoading ? 'Syncing...' : 'Sync'}
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1">
        <label className="text-sm font-medium text-gray-700">Branch:</label>
        <select
          value={currentBranch || ''}
          onChange={(e) => handleBranchChange(e.target.value)}
          disabled={disabled || loading}
          className="text-sm border border-gray-300 rounded px-2 py-1 bg-white disabled:bg-gray-100"
        >
          {branches.map(branch => (
            <option key={branch} value={branch}>
              {branch}
            </option>
          ))}
        </select>
      </div>
      
      <button
        onClick={handleSync}
        disabled={disabled || syncLoading}
        className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
      >
        {syncLoading ? 'Syncing...' : 'Sync'}
      </button>
      
      {loading && (
        <span className="text-sm text-gray-500">Loading branches...</span>
      )}
    </div>
  )
}
