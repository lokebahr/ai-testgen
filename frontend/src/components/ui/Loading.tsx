import { useEffect, useState } from "react";

export default function Loading() {
    const [letters, setLetters] = useState(0);
    const word = "test";

    useEffect(() => {
        const interval = setInterval(() => {
            setLetters(l => (l + 1) % (word.length + 1));
        }, 250);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="fixed inset-0 flex items-center justify-center z-50">
            <div className="bg-gray-900 text-green-400 rounded shadow p-2 w-28 h-16 flex flex-col justify-center items-center">
                <div className="font-mono text-xs tracking-widest text-center select-none">
                    {word.slice(0, letters).split("").join(" ")}
                </div>
                <div className="text-gray-500 text-xs mt-1">$</div>
            </div>
        </div>
    );
}