import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import TestCases from './pages/TestCases'
import ProjectInit from './pages/ProjectInit'
import ProjectWorkspace from './pages/ProjectWorkspace'


export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b p-4 flex gap-4 shadow">
        <Link to="/" className="text-blue-600 hover:underline">Home</Link>
        <Link to="/init" className="text-blue-600 hover:underline">New Project</Link>
        <Link to="/legacy" className="text-blue-600 hover:underline">Legacy Mode</Link>
      </nav>

      <Routes>
        <Route path="/" element={<ProjectInit />} />
        <Route path="/init" element={<ProjectInit />} />
        <Route path="/project/:projectId" element={<ProjectWorkspace />} />
        <Route path="/legacy" element={<Home />} />
        <Route path="/testcases" element={<TestCases />} />
      </Routes>
    </div>
  );
}
