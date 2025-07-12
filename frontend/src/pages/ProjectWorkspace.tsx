import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import Header from '../components/Header'
import Loading from '../components/ui/Loading'

interface FileTreeNode {
  name: string
  path: string
  type: 'file' | 'dir'
  children?: FileTreeNode[]
}

interface ProjectState {
  projectId: string
  fileTree: FileTreeNode[]
  selectedFile: string | null
  fileContent: string
  testResult: any
  loading: boolean
}

const FileTreeComponent = ({ 
  nodes, 
  onSelectFile, 
  selectedFile 
}: { 
  nodes: FileTreeNode[], 
  onSelectFile: (path: string) => void,
  selectedFile: string | null
}) => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set([]))

  const toggleExpanded = (path: string) => {
    const newExpanded = new Set(expanded)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpanded(newExpanded)
  }

  const renderNode = (node: FileTreeNode, depth = 0) => {
    const isExpanded = expanded.has(node.path)
    const isSelected = selectedFile === node.path
    
    return (
      <div key={node.path} style={{ marginLeft: depth * 20 }}>
        <div
          className={`flex items-center py-1 px-2 cursor-pointer hover:bg-gray-100 rounded ${
            isSelected ? 'bg-blue-100' : ''
          }`}
          onClick={() => {
            if (node.type === 'dir') {
              toggleExpanded(node.path)
            } else {
              onSelectFile(node.path)
            }
          }}
        >
          {node.type === 'dir' ? (
            <>
              <span className="mr-1">{isExpanded ? '📂' : '📁'}</span>
              <span>{node.name}</span>
            </>
          ) : (
            <>
              <span className="mr-1">📄</span>
              <span>{node.name}</span>
            </>
          )}
        </div>
        {node.type === 'dir' && isExpanded && node.children && (
          <div>
            {node.children.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="border rounded p-4 bg-white">
      <h3 className="font-medium mb-2">Project Files</h3>
      <div className="max-h-64 overflow-y-auto">
        {nodes.map(node => renderNode(node))}
      </div>
    </div>
  )
}

export default function ProjectWorkspace() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [state, setState] = useState<ProjectState>({
    projectId: projectId!,
    fileTree: [],
    selectedFile: null,
    fileContent: '',
    testResult: null,
    loading: true
  })

  useEffect(() => {
    loadFileTree()
  }, [projectId])

  const loadFileTree = async () => {
    try {
      setState(prev => ({ ...prev, loading: true }))
      const response = await fetch(`http://localhost:5000/api/projects/${projectId}/files`)
      const data = await response.json()
      
      if (response.ok) {
        setState(prev => ({ ...prev, fileTree: data, loading: false }))
      } else {
        alert(`Error loading files: ${data.error}`)
        setState(prev => ({ ...prev, loading: false }))
      }
    } catch (err) {
      console.error('Error loading file tree:', err)
      setState(prev => ({ ...prev, loading: false }))
    }
  }

  const loadFileContent = async (filePath: string) => {
    try {
      setState(prev => ({ ...prev, loading: true, selectedFile: filePath }))
      const response = await fetch(`http://localhost:5000/api/projects/${projectId}/files/${filePath}`)
      const data = await response.json()
      
      if (response.ok) {
        setState(prev => ({ ...prev, fileContent: data.content, loading: false }))
      } else {
        alert(`Error loading file: ${data.error}`)
        setState(prev => ({ ...prev, loading: false }))
      }
    } catch (err) {
      console.error('Error loading file content:', err)
      setState(prev => ({ ...prev, loading: false }))
    }
  }

  const runTests = async () => {
    if (!state.selectedFile) {
      alert('Please select a file first')
      return
    }

    try {
      setState(prev => ({ ...prev, loading: true }))
      const response = await fetch(`http://localhost:5000/api/projects/${projectId}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: state.selectedFile,
          language: 'python',
          framework: 'pytest'
        })
      })
      
      const data = await response.json()
      setState(prev => ({ ...prev, testResult: data, loading: false }))
      
    } catch (err) {
      console.error('Error running tests:', err)
      setState(prev => ({ ...prev, loading: false }))
    }
  }

  const renderTestResult = () => {
    if (!state.testResult) return null

    const { status, execution_result, analysis_markdown, fix_markdown } = state.testResult

    return (
      <div className="border rounded p-4 bg-white">
        <h3 className="font-medium mb-2">Test Results</h3>
        
        {status === 'ALL_TESTS_PASS' ? (
          <div className="text-green-600">
            <p className="font-medium">✅ All tests passed!</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-red-600">
              <p className="font-medium">❌ Tests failed</p>
            </div>
            
            {execution_result && (
              <div>
                <h4 className="font-medium mb-1">Execution Output:</h4>
                <pre className="bg-gray-100 p-2 rounded text-sm overflow-x-auto">
                  {execution_result.output}
                </pre>
              </div>
            )}
            
            {analysis_markdown && (
              <div>
                <h4 className="font-medium mb-1">Analysis:</h4>
                <div className="bg-yellow-50 p-2 rounded">
                  <pre className="text-sm whitespace-pre-wrap">{analysis_markdown}</pre>
                </div>
              </div>
            )}
            
            {fix_markdown && (
              <div>
                <h4 className="font-medium mb-1">Suggested Fix:</h4>
                <div className="bg-blue-50 p-2 rounded">
                  <pre className="text-sm whitespace-pre-wrap">{fix_markdown}</pre>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <Layout padding="lg" width="full">
      <div className="flex justify-between items-center mb-6">
        <Header title={`Project: ${projectId?.substring(0, 8) || 'Unknown'}...`} size="h1" />
        <button
          onClick={() => navigate('/')}
          className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
        >
          New Project
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: File Tree */}
        <div>
          <FileTreeComponent 
            nodes={state.fileTree} 
            onSelectFile={loadFileContent}
            selectedFile={state.selectedFile}
          />
        </div>

        {/* Right Column: File Content and Actions */}
        <div className="space-y-4">
          {state.selectedFile && (
            <div className="border rounded p-4 bg-white">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium">File: {state.selectedFile}</h3>
                <button
                  onClick={runTests}
                  disabled={state.loading}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {state.loading ? 'Running...' : 'Run Tests'}
                </button>
              </div>
              <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto max-h-64">
                {state.fileContent}
              </pre>
            </div>
          )}

          {renderTestResult()}
        </div>
      </div>

      {state.loading && <Loading />}
    </Layout>
  )
}
