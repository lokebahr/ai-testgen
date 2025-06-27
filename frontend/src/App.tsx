import { Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import TestCases from './pages/TestCases'


export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b p-4 flex gap-4 shadow">
        <Link to="/" className="text-blue-600 hover:underline">Hem</Link>
      
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/testcases" element={<TestCases />} />
        
      </Routes>
    </div>
  );
}
