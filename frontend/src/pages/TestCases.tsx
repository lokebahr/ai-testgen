import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Layout from "../components/Layout";
import Header from "../components/Header";


export default function TestCases() {
    const [tests, setTests] = useState<string[]>([""]);
    const navigate = useNavigate();
    const location = useLocation();
    const generatedTests = location.state?.generatedTests || "";

    
    return (
        <Layout padding="lg" width="lg">
            <Header title="Testfall" size="h1" />
            <div className="max-w-3xl mx-auto mt-8">
                <pre className="bg-gray-900 text-green-200 rounded p-4 overflow-x-auto whitespace-pre-wrap text-sm">
                    {generatedTests}
                </pre>
            </div>
            <div className="flex justify-end mb-2">
                <button
                    className="btn btn-xs bg-green-600 text-white hover:bg-green-700 rounded flex items-center gap-1 px-3 py-1 shadow"
                    onClick={() => {
                        navigator.clipboard.writeText(generatedTests);
                    }}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16h8M8 12h8m-7 8h6a2 2 0 002-2V7a2 2 0 00-2-2h-6a2 2 0 00-2 2v11a2 2 0 002 2z" /></svg>
                    Kopiera testkod
                </button>
            </div>
        </Layout>
    );
}