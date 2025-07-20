interface TestPlanModalProps {
  testPlan: string[]
  onApprove: () => void
  onRegenerate: () => void
  loading: boolean
  loadingText: string
  onClose?: () => void
}

export default function TestPlanModal({ 
  testPlan, 
  onApprove, 
  onRegenerate, 
  loading, 
  loadingText,
  onClose 
}: TestPlanModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Test Plan</h2>
          {onClose && (
            <button 
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          )}
        </div>
        
        <div className="space-y-2 mb-6">
          <p className="text-sm text-gray-600 mb-3">
            The following tests will be generated for your code:
          </p>
          {testPlan.map((test, index) => (
            <div key={index} className="flex items-start">
              <span className="mr-2 mt-1">•</span>
              <span className="text-sm">{test}</span>
            </div>
          ))}
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={onApprove}
            disabled={loading}
            className="flex-1 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 disabled:bg-gray-400"
          >
            {loading && loadingText.includes('Generating') ? loadingText : 'Approve & Generate Tests'}
          </button>
          <button
            onClick={onRegenerate}
            disabled={loading}
            className="flex-1 bg-yellow-600 text-white py-2 px-4 rounded hover:bg-yellow-700 disabled:bg-gray-400"
          >
            {loading && loadingText.includes('Planning') ? loadingText : 'Regenerate Plan'}
          </button>
        </div>
      </div>
    </div>
  )
}
