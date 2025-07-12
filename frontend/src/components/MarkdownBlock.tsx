import React from "react";
import ReactMarkdown from "react-markdown";

export default function MarkdownBlock({ children }: { children: string }) {
  return (
    <div className="prose max-w-none">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  );
}
