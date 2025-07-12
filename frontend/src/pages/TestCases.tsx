import { useState } from "react";
import { useLocation } from "react-router-dom";
import Layout from "../components/Layout";
import Header from "../components/Header";
import MarkdownBlock from "../components/MarkdownBlock";

export default function TestCases() {
    const location = useLocation();
    // Expect: { testCode, testPlan }
    const testCode = location.state?.testCode || "";
    const testPlan = location.state?.testPlan || [];
    const [pytestOutput, setPytestOutput] = useState("");
    const [review, setReview] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const handleDownload = () => {
        const blob = new Blob([testCode], { type: "text/x-python" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "test_generated.py";
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleReview = async () => {
        setLoading(true);
        setReview(null);
        try {
            const resp = await fetch("http://localhost:5000/review", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ passed: false, output: pytestOutput }),
            });
            const data = await resp.json();
            console.log("Review response:", data);
            setReview(data);
        } catch (e) {
            console.error("Review error:", e);
            setReview({ error: "Kunde inte analysera resultatet." });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout padding="lg" width="lg">
            <Header title="Testresultat" size="h1" />
            <div className="max-w-3xl mx-auto mt-8 space-y-6">
                <div>
                    <h2 className="font-bold mb-2">Testplan</h2>
                    <ul className="list-disc ml-6 text-green-700">
                        {testPlan.map((t: string, i: number) => (
                            <li key={i}>{t}</li>
                        ))}
                    </ul>
                </div>
                <div>
                    <h2 className="font-bold mb-2">Genererad testkod</h2>
                    <pre className="bg-gray-900 text-green-200 rounded p-4 overflow-x-auto whitespace-pre-wrap text-sm">
                        {testCode}
                    </pre>
                    <button className="btn btn-xs bg-blue-600 text-white rounded mt-2" onClick={handleDownload}>
                        Ladda ner testfil
                    </button>
                </div>
                <div>
                    <h2 className="font-bold mb-2">Klistra in pytest-resultat</h2>
                    <textarea
                        className="w-full h-32 border rounded p-2 font-mono"
                        value={pytestOutput}
                        onChange={e => setPytestOutput(e.target.value)}
                        placeholder="Klistra in utdata från pytest här..."
                    />
                    <button
                        className="btn btn-xs bg-green-600 text-white rounded mt-2"
                        onClick={handleReview}
                        disabled={loading || !pytestOutput.trim()}
                    >
                        Analysera resultat
                    </button>
                </div>
                {review && (
                    <div>
                        <h2 className="font-bold mb-2">AI-analys</h2>
                        {review.analysis_markdown && (
                            <div className="mb-4">
                                <h3 className="font-semibold">Orsak till fel</h3>
                                <MarkdownBlock>{review.analysis_markdown}</MarkdownBlock>
                            </div>
                        )}
                        {review.fix_markdown && (
                            <div className="mb-4">
                                <h3 className="font-semibold">Föreslagen kodändring</h3>
                                <pre className="bg-gray-900 text-green-200 rounded p-4 overflow-x-auto whitespace-pre-wrap text-sm">
                                    {review.fix_markdown.replace(/```python\n?/g, '').replace(/```\n?/g, '')}
                                </pre>
                            </div>
                        )}
                        {!review.analysis_markdown && !review.fix_markdown && (
                            <pre className="bg-gray-900 text-yellow-200 rounded p-4 overflow-x-auto whitespace-pre-wrap text-sm">
                                {typeof review === "string" ? review : JSON.stringify(review, null, 2)}
                            </pre>
                        )}
                    </div>
                )}
            </div>
        </Layout>
    );
}