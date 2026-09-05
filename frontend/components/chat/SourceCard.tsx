import React, { useState } from "react";
import { Source } from "@/lib/types";
import { ExternalLink, ChevronDown, ChevronUp, BookOpen } from "lucide-react";

interface SourceCardProps {
  sources: Source[];
}

export const SourceCard: React.FC<SourceCardProps> = ({ sources }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 pt-3 border-t border-surface-200">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-xs font-semibold text-zinc-400 hover:text-zinc-200 transition-colors py-1"
      >
        <span className="flex items-center gap-1.5">
          <BookOpen className="w-3.5 h-3.5 text-primary" />
          Sources Cited ({sources.length})
        </span>
        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2">
          {sources.map((src, idx) => (
            <div
              key={src.id || idx}
              className="p-2.5 rounded-lg bg-surface-100 border border-surface-200 text-xs hover:border-surface-300 transition-colors"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold text-zinc-200 truncate">
                  [{idx + 1}] {src.source_title}
                </span>
                {src.url && (
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:text-primary-hover inline-flex items-center gap-0.5 flex-shrink-0"
                  >
                    Link <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                )}
              </div>
              <div className="text-zinc-400 mt-1 font-medium">Guest: {src.guest}</div>
              {src.snippet && (
                <div className="mt-1 text-zinc-400/90 italic bg-surface-50 p-1.5 rounded border border-surface-200/50">
                  "{src.snippet}"
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
