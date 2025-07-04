import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Layout from "../components/Layout"
import Header from "../components/Header"
import CodeInput from "../components/CodeInput"
import TestPlanModal from "../components/TestPlanModal"
import Loading from "../components/ui/Loading"

export default function Home() {
    const [code, setCode] = useState("")
    const [language, setLanguage] = useState("python")
    const [framework, setFramework] = useState("pytest")
    const [modalOpen, setModalOpen] = useState(false)
    const [testIdeas, setTestIdeas] = useState<string[]>([])
    const [filename, setFilename] = useState("")
    const [showFilenameInput, setShowFilenameInput] = useState(false)
    const [pendingPlan, setPendingPlan] = useState<string[]>([])
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const response = await fetch("http://localhost:5000/api/testplan", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ code, language, framework }),
            });
            const data = await response.json();
            if (response.ok) {
                // Parse as JSON array
                let ideas: string[] = [];
                try {
                    ideas = JSON.parse(data.plan);
                } catch {
                    ideas = [];
                }
                setTestIdeas(ideas);
                setModalOpen(true);
            } else {
                console.error("Error:", data.error);
            }
        } catch (err) {
            console.error("Network error:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleConfirm = (plan: string[]) => {
        setPendingPlan(plan);
        setShowFilenameInput(true);
    };

    const handleFilenameSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setShowFilenameInput(false);
        setLoading(true);
        try {
            const response = await fetch("http://localhost:5000/api/test_creation", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    code,
                    testPlan: pendingPlan,
                    filename,
                }),
            });
            const data = await response.json();
            if (data.tests) {
                navigate("/testcases", { state: { generatedTests: data.tests } });
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
                onChangeCode={setCode}
                onChangeLanguage={setLanguage}
                onChangeFramework={setFramework}
                onGenerate={handleGenerate}
            />
            <TestPlanModal
                open={modalOpen}
                onClose={() => setModalOpen(false)}
                initialTests={testIdeas}
                onConfirm={handleConfirm}
            />
            {loading && <Loading />}
            {showFilenameInput && !loading && (
                <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
                    <form onSubmit={handleFilenameSubmit} className="bg-white rounded-lg shadow-lg p-6 w-full max-w-sm flex flex-col gap-4">
                        <label className="font-semibold">Filnamn för kodfilen:</label>
                        <input
                            className="border rounded px-3 py-2"
                            value={filename}
                            onChange={e => setFilename(e.target.value)}
                            placeholder="exempel.py"
                            required
                        />
                        <button className="btn btn-primary" type="submit">Generera tester</button>
                    </form>
                </div>
            )}
        </Layout>
    )
}