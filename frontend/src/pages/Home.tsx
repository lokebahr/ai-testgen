
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Layout from "../components/Layout"
import Header from "../components/Header"
import CodeInput from "../components/CodeInput"
import TestPlanModal from "../components/TestPlanModal"
import Loading from "../components/ui/Loading"

export default function Home() {
    const [code, setCode] = useState("");
    const [language, setLanguage] = useState("python");
    const [framework, setFramework] = useState("pytest");
    const [filename, setFilename] = useState("code.py");
    const [modalOpen, setModalOpen] = useState(false);
    const [testIdeas, setTestIdeas] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    // Step 1: Plan
    const handleGenerate = async () => {
        setLoading(true);
        try {
            const response = await fetch("http://localhost:5000/plan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, language, framework }),
            });
            const data = await response.json();
            if (data.tests) {
                setTestIdeas(data.tests);
                setModalOpen(true);
            } else if (data.error) {
                alert(`Fel: ${data.error} (steg: ${data.step})`);
            }
        } catch (err) {
            console.error("Network error:", err);
        } finally {
            setLoading(false);
        }
    };

    // Update filename when language changes
    const handleLanguageChange = (newLanguage: string) => {
        setLanguage(newLanguage);
        
        // Update filename extension based on language
        const currentName = filename.split('.')[0] || 'code';
        let newExtension = '';
        
        switch (newLanguage) {
            case 'python':
                newExtension = '.py';
                break;
            case 'javascript':
                newExtension = '.js';
                break;
            case 'java':
                newExtension = '.java';
                break;
            default:
                newExtension = '.txt';
        }
        
        setFilename(currentName + newExtension);
    };

    // Step 2: User confirms test plan
    const handleConfirm = async (plan: string[]) => {
        setModalOpen(false);
        setLoading(true);
        try {
            const response = await fetch("http://localhost:5000/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, tests: plan, filename }),
            });
            const data = await response.json();
            if (data.test_code) {
                navigate("/testcases", { state: { testCode: data.test_code, testPlan: plan } });
            } else if (data.error) {
                alert(`Fel: ${data.error} (steg: ${data.step})`);
            }
        } catch (err) {
            console.error("Network error:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout padding="lg" width="lg">
            <Header title="AI Testgenerator" size="h1"/>
            <CodeInput 
                code={code}
                language={language}
                framework={framework}
                filename={filename}
                onChangeCode={setCode}
                onChangeLanguage={handleLanguageChange}
                onChangeFramework={setFramework}
                onChangeFilename={setFilename}
                onGenerate={handleGenerate}
            />
            <TestPlanModal
                open={modalOpen}
                onClose={() => setModalOpen(false)}
                initialTests={testIdeas}
                onConfirm={handleConfirm}
            />
            {loading && <Loading />}
        </Layout>
    );
}