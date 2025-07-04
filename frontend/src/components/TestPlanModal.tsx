import React, { useState, useEffect } from "react";
import TestCard from "./TestCard.tsx";

interface TestPlanModalProps {
    open: boolean;
    onClose: () => void;
    initialTests: string[];
    onConfirm: (tests: string[]) => void;
}

export default function TestPlanModal({ open, onClose, initialTests, onConfirm }: TestPlanModalProps) {
    const [tests, setTests] = useState<string[]>(initialTests);

    useEffect(() => {
        setTests(initialTests);
    }, [initialTests, open]);

    const handleChange = (idx: number, value: string) => {
        setTests(tests => tests.map((t, i) => i === idx ? value : t));
    };

    const handleDelete = (idx: number) => {
        setTests(tests => tests.filter((_, i) => i !== idx));
    };

    const handleAdd = () => {
        setTests(tests => [...tests, ""]);
    };

    const handleConfirm = () => {
        onConfirm(tests.filter(t => t.trim() !== ""));
        onClose();
    };

    if (!open) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-lg">
                <h2 className="text-xl font-bold mb-4">Suggested Tests</h2>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                    {tests.map((test, idx) => (
                        <TestCard
                            key={idx}
                            value={test}
                            onChange={v => handleChange(idx, v)}
                            onDelete={() => handleDelete(idx)}
                        />
                    ))}
                </div>
                <div className="flex justify-between mt-4">
                    <button className="btn btn-outline" onClick={handleAdd}>Add Test</button>
                    <div>
                        <button className="btn btn-secondary mr-2" onClick={onClose}>Cancel</button>
                        <button className="btn btn-primary" onClick={handleConfirm}>Confirm</button>
                    </div>
                </div>
            </div>
        </div>
    );
}