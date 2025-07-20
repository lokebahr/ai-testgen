import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import Header from '../components/Header'
import Loading from '../components/ui/Loading'
import TestPlanModal from '../components/TestPlanModal'

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
  testPlan: string[] | null
  testResult: any
  loading: boolean
  currentStep: 'idle' | 'planning' | 'generating' | 'executing' | 'reviewing'
  modalOpen: boolean
  workflowId: string | null
  workflowStatus: {
    step: string
    status: string
    message: string
    progress: number
  } | null
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
    testPlan: null,
    testResult: null,
    loading: true,
    currentStep: 'idle',
    modalOpen: false,
    workflowId: null,
    workflowStatus: null
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

  const planTests = async () => {
    if (!state.selectedFile) {
      alert('Please select a file first')
      return
    }

    try {
      setState(prev => ({ ...prev, loading: true, currentStep: 'planning', testPlan: null, testResult: null }))
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
      
      if (response.ok) {
        setState(prev => ({ 
          ...prev, 
          testPlan: data.test_plan, 
          loading: false, 
          currentStep: 'idle',
          modalOpen: true 
        }))
      } else {
        alert(`Error planning tests: ${data.error}`)
        setState(prev => ({ ...prev, loading: false, currentStep: 'idle' }))
      }
      
    } catch (err) {
      console.error('Error planning tests:', err)
      setState(prev => ({ ...prev, loading: false, currentStep: 'idle' }))
    }
  }

  const regeneratePlan = () => {
    // Close modal and replan
    setState(prev => ({ ...prev, modalOpen: false }))
    planTests()
  }

  const approvePlan = async (approvedTests: string[]) => {
    if (!state.selectedFile) {
      alert('No file selected')
      return
    }

    const workflowId = `${projectId}_${Date.now()}`

    try {
      setState(prev => ({ 
        ...prev, 
        loading: true, 
        currentStep: 'generating', 
        modalOpen: false,
        workflowId,
        workflowStatus: { step: 'initializing', status: 'running', message: 'Starting workflow...', progress: 0 }
      }))

      startWorkflowPolling(workflowId)
      
      const response = await fetch(`http://localhost:5000/api/projects/${projectId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: state.selectedFile,
          test_plan: approvedTests,
          workflow_id: workflowId
        })
      })
      
      const data = await response.json()
      setState(prev => ({ 
        ...prev, 
        testResult: data, 
        loading: false, 
        currentStep: 'idle',
        workflowStatus: null
      }))
      
    } catch (err) {
      console.error('Error running tests:', err)
      setState(prev => ({ 
        ...prev, 
        loading: false, 
        currentStep: 'idle',
        workflowStatus: null
      }))
    }
  }

  const startWorkflowPolling = (workflowId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/workflow/${workflowId}/status`)
        const status = await response.json()
        
        setState(prev => ({ ...prev, workflowStatus: status }))
        
        if (status.status === 'completed' || status.status === 'failed' || status.status === 'success') {
          clearInterval(pollInterval)
        }
      } catch (err) {
        console.error('Error polling workflow status:', err)
        clearInterval(pollInterval)
      }
    }, 1000)

    setTimeout(() => clearInterval(pollInterval), 30000)
  }

  const renderTestResult = () => {
    if (!state.testResult) return null

    const { status, execution_result, issues, summary, fixed_code, analysis_markdown, fix_markdown } = state.testResult

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
              {summary && (
                <p className="text-sm mt-1">{summary}</p>
              )}
            </div>
            
            {execution_result && (
              <div>
                <h4 className="font-medium mb-1">Execution Output:</h4>
                <pre className="bg-gray-100 p-2 rounded text-sm overflow-x-auto">
                  {execution_result.output}
                </pre>
              </div>
            )}
            
            {issues && issues.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Issues Found:</h4>
                <div className="space-y-3">
                  {issues.map((issue: any, index: number) => (
                    <div key={index} className="bg-red-50 p-3 rounded border-l-4 border-red-400">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium text-red-800">{issue.test_name}</span>
                        <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded">
                          {issue.error_type}
                        </span>
                      </div>
                      <p className="text-sm text-red-700 mb-2">{issue.description}</p>
                      {(issue.expected || issue.actual) && (
                        <div className="text-xs text-red-600 space-y-1">
                          {issue.expected && <div><strong>Expected:</strong> {issue.expected}</div>}
                          {issue.actual && <div><strong>Actual:</strong> {issue.actual}</div>}
                        </div>
                      )}
                      {issue.cause && (
                        <div className="text-xs text-red-600 mt-1">
                          <strong>Cause:</strong> {issue.cause}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {fixed_code && (
              <div>
                <h4 className="font-medium mb-1">Suggested Fix:</h4>
                <div className="bg-green-50 border border-green-200 rounded">
                  <pre className="p-3 text-sm overflow-x-auto"><code>{fixed_code}</code></pre>
                </div>
              </div>
            )}

            {!issues && analysis_markdown && (
              <div>
                <h4 className="font-medium mb-1">Analysis:</h4>
                <div className="bg-yellow-50 p-2 rounded">
                  <pre className="text-sm whitespace-pre-wrap">{analysis_markdown}</pre>
                </div>
              </div>
            )}
            
            {!fixed_code && fix_markdown && (
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

  const renderWorkflowProgress = () => {
    if (!state.workflowStatus || !state.loading) return null

    const { step, message, progress } = state.workflowStatus
    
    const stepIcons = {
      initializing: '🔧',
      generating: '🤖',
      executing: '⚡',
      reviewing: '🔍',
      completed: '✅'
    }

    return (
      <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{stepIcons[step as keyof typeof stepIcons] || '⏳'}</span>
            <span className="font-medium capitalize">{step}</span>
          </div>
          <span className="text-sm text-blue-600">{progress}%</span>
        </div>
        <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <p className="text-sm text-blue-700">{message}</p>
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
          {renderWorkflowProgress()}
          
          {state.selectedFile && (
            <div className="border rounded p-4 bg-white">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium">File: {state.selectedFile}</h3>
                <button
                  onClick={planTests}
                  disabled={state.loading}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {state.loading && state.currentStep === 'planning' ? 'Planning...' : 'Plan Tests'}
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

      <TestPlanModal
        open={state.modalOpen}
        onClose={() => setState(prev => ({ ...prev, modalOpen: false }))}
        initialTests={state.testPlan || []}
        onConfirm={approvePlan}
        onRegenerate={regeneratePlan}
      />

      {state.loading && <Loading />}
    </Layout>
  )
}
