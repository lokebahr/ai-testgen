import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import Header from '../components/Header'
import Loading from '../components/ui/Loading'

interface Project {
  id: string
  title: string
  git_repo?: string
  branch?: string
  mode: string
  created_at: string
  updated_at: string
  files: any[]
}

export default function ProjectsList() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:5000/api/db/projects')
      const data = await response.json()
      
      if (response.ok) {
        setProjects(data)
      } else {
        console.error('Error loading projects:', data.error)
      }
    } catch (err) {
      console.error('Network error:', err)
    } finally {
      setLoading(false)
    }
  }

  const deleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project?')) return
    
    try {
      const response = await fetch(`http://localhost:5000/api/db/projects/${projectId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        loadProjects() // Reload the list
      } else {
        const data = await response.json()
        alert(`Error deleting project: ${data.error}`)
      }
    } catch (err) {
      console.error('Error deleting project:', err)
      alert('Failed to delete project')
    }
  }

  const getStatusSummary = (files: any[]) => {
    const completed = files.filter(f => f.test_status === 'completed').length
    const failed = files.filter(f => f.test_status === 'failed').length
    const untested = files.filter(f => f.test_status === 'untested').length
    
    return { completed, failed, untested, total: files.length }
  }

  if (loading) return <Loading />

  return (
    <Layout padding="lg" width="lg">
      <div className="flex justify-between items-center mb-6">
        <Header title="My Projects" size="h1" />
        <button
          onClick={() => navigate('/init')}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          New Project
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">No projects found</p>
          <button
            onClick={() => navigate('/init')}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Create Your First Project
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((project) => {
            const status = getStatusSummary(project.files)
            
            return (
              <div key={project.id} className="border rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="text-lg font-semibold">{project.title}</h3>
                    <div className="text-sm text-gray-600">
                      <span className="mr-4">Mode: {project.mode}</span>
                      {project.git_repo && (
                        <span className="mr-4">Repo: {project.git_repo}</span>
                      )}
                      {project.branch && (
                        <span>Branch: {project.branch}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => navigate(`/project/${project.id}`)}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                    >
                      Open
                    </button>
                    <button
                      onClick={() => deleteProject(project.id)}
                      className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                
                <div className="flex gap-4 text-sm">
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                    {status.completed} Completed
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                    {status.failed} Failed
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                    {status.untested} Untested
                  </span>
                  <span className="text-gray-500">
                    Total: {status.total} files
                  </span>
                </div>
                
                <div className="text-xs text-gray-400 mt-2">
                  Created: {new Date(project.created_at).toLocaleDateString()}
                  {' • '}
                  Updated: {new Date(project.updated_at).toLocaleDateString()}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </Layout>
  )
}
