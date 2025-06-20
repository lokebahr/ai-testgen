import React from "react";


//Variabler vi behövers sen
type Props = {
    code: string
    language: string
    framework: string
    onChangeCode: (value:string) => void
    onChangeLanguage: (value:string) => void
    onChangeFramework: (value: string) => void
    onGenerate: () => void
}

const CodeInput: React.FC<Props> = ({
    code,
    language,
    framework,
    onChangeCode,
    onChangeLanguage,
    onChangeFramework,
    onGenerate,
}) => {
    //spacing
    return (
        <div className="space-y-4">
    
        <label className="block text-sm font-medium mb-1">
             Kod
        </label>

        {/* hittar allt sånt https://tailwindcss.com/docs/installation/using-vite */}
        <textarea
        className="
            w-full             
            h-64                
            p-4                
            font-mono           
            border              
            border-zinc-300     
            dark:border-zinc-700
            bg-white            
            dark:bg-zinc-800    
            rounded-md          
            resize-none         
            focus:outline-none  
            focus:ring-2        
            focus:ring-blue-500 
        
    
        "
        placeholder="Klistra in din kod här..."
        value={code}  
        onChange={(e) => onChangeCode(e.target.value)} // skicka vidare ändring till föräldern
        />
        <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
                <label className="block text-sm font-medium mb-1">
                    Språk
                </label>
                <select
                    className="w-full p-2 border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-md"
                    value={language}
                    onChange={(e) => onChangeLanguage(e.target.value)}>
                        <option value="python">Python</option>
                        <option value="javascript">JavaScript</option>
                        <option value="java">Java</option>
                    </select>
            </div>

            <div className="flex-1">
                <label className="block text-sm font-medium mb-1">
                    Test-ramverk
                </label>
                 <select
                    className="w-full p-2 border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 rounded-md"
                    value={framework}
                    onChange={(e) => onChangeFramework(e.target.value)}
                >
                    <option value="pytest">pytest</option>
                    <option value="unittest">unittest</option>
                    <option value="jest">jest</option>
                    <option value="junit">JUnit</option>
                </select>
            </div>
        </div>

        

        <button
            onClick = {onGenerate}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition">
                Generera testfall
            </button>

    </div>
    );
}

export default CodeInput;