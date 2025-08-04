import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import Header from '../components/Header'
import Loading from '../components/ui/Loading'

export default function ProjectInit() {
  const [mode, setMode] = useState<'single' | 'git'>('single')
  const [title, setTitle] = useState('')
  const [fileContent, setFileContent] = useState('')
  const [filename, setFilename] = useState('main.py')
  const [gitUrl, setGitUrl] = useState('')
  const [branch, setBranch] = useState('')
  const [availableBranches, setAvailableBranches] = useState<string[]>([])
  const [loadingBranches, setLoadingBranches] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleInit = async () => {
    setLoading(true)
    try {
      const payload = mode === 'single' 
        ? { mode, title: title || `Single File: ${filename}`, file: fileContent, filename }
        : { mode, title: title || `Git: ${gitUrl.split('/').pop() || 'Repository'}`, git_url: gitUrl, ...(branch && { branch }) }

      const response = await fetch('http://localhost:5000/api/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      const data = await response.json()
      
      if (response.ok) {
        // Navigate to project workspace with project_id
        navigate(`/project/${data.project_id}`)
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (err) {
      console.error('Network error:', err)
      alert('Failed to initialize project')
    } finally {
      setLoading(false)
    }
  }

  const fetchBranches = async (url: string) => {
    if (!url) return
    
    setLoadingBranches(true)
    try {
      const response = await fetch('http://localhost:5000/api/git/branches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ git_url: url })
      })
      
      const data = await response.json()
      if (response.ok) {
        setAvailableBranches(data.branches)
      } else {
        setAvailableBranches([])
      }
    } catch (err) {
      setAvailableBranches([])
    } finally {
      setLoadingBranches(false)
    }
  }

  useEffect(() => {
    if (mode === 'git' && gitUrl) {
      const timer = setTimeout(() => {
        fetchBranches(gitUrl)
      }, 500) // Debounce API call by 500ms

      return () => clearTimeout(timer)
    } else {
      setAvailableBranches([])
    }
  }, [gitUrl, mode])

  return (
    <Layout padding="lg" width="lg">
      <Header title="Initialize Project" size="h1" />
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Project Mode</label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="single"
                checked={mode === 'single'}
                onChange={(e) => setMode(e.target.value as 'single')}
                className="mr-2"
              />
              Single File
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="git"
                checked={mode === 'git'}
                onChange={(e) => setMode(e.target.value as 'git')}
                className="mr-2"
              />
              Git Repository
            </label>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Project Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={mode === 'single' ? `Single File: ${filename}` : 'Enter project title...'}
            className="w-full p-2 border border-gray-300 rounded"
          />
        </div>

        {mode === 'single' ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Filename</label>
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded"
                placeholder="main.py"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Code Content</label>
              <textarea
                value={fileContent}
                onChange={(e) => setFileContent(e.target.value)}
                className="w-full h-64 p-3 border border-gray-300 rounded font-mono text-sm"
                placeholder="Enter your code here..."
              />
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Git Repository URL</label>
              <input
                type="url"
                value={gitUrl}
                onChange={(e) => {
                  setGitUrl(e.target.value)
                  setBranch('')
                  setAvailableBranches([])
                }}
                onBlur={() => fetchBranches(gitUrl)}
                className="w-full p-2 border border-gray-300 rounded"
                placeholder="https://github.com/username/repository.git"
              />
              <p className="text-sm text-gray-600 mt-1">
                Enter a public Git repository URL to clone and analyze
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">
                Branch {loadingBranches && '(loading...)'}
              </label>
              {availableBranches.length > 0 ? (
                <select
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  <option value="">Select a branch (optional)</option>
                  {availableBranches.map((branchName) => (
                    <option key={branchName} value={branchName}>
                      {branchName}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="main, develop, feature/branch-name"
                  disabled={loadingBranches}
                />
              )}
              <p className="text-sm text-gray-600 mt-1">
                Leave empty to use the default branch
              </p>
            </div>
            {loadingBranches && <Loading />}
            {!loadingBranches && availableBranches.length > 0 && (
              <div>
                <label className="block text-sm font-medium mb-2">Available Branches</label>
                <select
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  <option value="">Select a branch</option>
                  {availableBranches.map((b) => (
                    <option key={b} value={b}>
                      {b}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        <button
          onClick={handleInit}
          disabled={loading || (mode === 'single' && !fileContent) || (mode === 'git' && !gitUrl)}
          className="w-full bg-yellow-500 text-black py-2 px-4 rounded hover:bg-yellow-600 disabled:bg-gray-400"
        >
          {loading ? 'Initializing...' : 'Initialize Project'}
        </button>
      </div>

      {loading && <Loading />}
    </Layout>
  )
}
