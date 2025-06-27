import { useState } from "react";
import {useNavigate} from "react-router-dom"
import { useLocation } from "react-router-dom";
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
        </Layout>
    );
}