import React from "react";

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  return (
    <div className="w-full h-full min-h-[450px] p-6 bg-surface-50 text-zinc-200 overflow-y-auto rounded-lg border border-surface-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
      {content}
    </div>
  );
};
