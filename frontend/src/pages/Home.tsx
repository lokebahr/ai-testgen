import { useState } from "react"
import Layout from "../components/Layout"
import Header from "../components/Header"
import CodeInput from "../components/CodeInput"

export default function Home() {
    const [code, setCode] = useState("")
    const [language, setLanguage] = useState("python")
    const [framework, setFramework] = useState("pytest")

    //enkel connection till backenden, bara med en hårdkodat exempel (ingen api ännu)
    const handleGenerate = async () => {
    try {
        const response = await fetch("http://localhost:5000/generate-ideas", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ code, language, framework }),
        });
        const data = await response.json();
        if (response.ok) {
            console.log("Test ideas:", data.test_ideas);
            
        } else {
            console.error("Error:", data.error);
        }
    } catch (err) {
        console.error("Network error:", err);
    }
};
    return (
        <Layout padding="lg" width="lg">

            <Header title="AI Testgenerator" size="h1"/>
            <CodeInput 
                code = {code}
                language={language}
                framework={framework}
                onChangeCode={setCode}
                onChangeLanguage={setLanguage}
                onChangeFramework={setFramework}
                onGenerate={handleGenerate}
            />
        </Layout>
    )
}