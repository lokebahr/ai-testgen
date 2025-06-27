import React from "react";

interface TestCardProps {
    value: string;
    onChange: (v: string) => void;
    onDelete: () => void;
}

export default function TestCard({ value, onChange, onDelete }: TestCardProps) {
    return (
        <div className="flex items-center bg-gray-100 rounded p-2 shadow">
            <input
                className="flex-1 bg-transparent border-none outline-none text-base"
                value={value}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value)}
            />
            <button className="ml-2 text-red-500 hover:text-red-700" onClick={onDelete}>
                ✕
            </button>
        </div>
    );
}