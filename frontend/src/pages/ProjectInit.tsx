import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import Header from '../components/Header'
import Loading from '../components/ui/Loading'

export default function ProjectInit() {
  const [mode, setMode] = useState<'single' | 'git'>('single')
  const [fileContent, setFileContent] = useState('')
  const [filename, setFilename] = useState('main.py')
  const [gitUrl, setGitUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleInit = async () => {
    setLoading(true)
    try {
      const payload = mode === 'single' 
        ? { mode, file: fileContent, filename }
        : { mode, git_url: gitUrl }

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
          <div>
            <label className="block text-sm font-medium mb-2">Git Repository URL</label>
            <input
              type="url"
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded"
              placeholder="https://github.com/username/repository.git"
            />
            <p className="text-sm text-gray-600 mt-1">
              Enter a public Git repository URL to clone and analyze
            </p>
          </div>
        )}

        <button
          onClick={handleInit}
          disabled={loading || (mode === 'single' && !fileContent) || (mode === 'git' && !gitUrl)}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? 'Initializing...' : 'Initialize Project'}
        </button>
      </div>

      {loading && <Loading />}
    </Layout>
  )
}
