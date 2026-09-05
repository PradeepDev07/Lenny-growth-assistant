import React, { useState } from "react";
import { Artifact } from "@/lib/types";
import { SandboxedHtmlFrame } from "./SandboxedHtmlFrame";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { Copy, Download, ExternalLink, X, Code2, Eye, FileText, Check } from "lucide-react";

interface ArtifactViewerProps {
  artifacts: Artifact[];
  activeArtifactId?: string;
  onSelectArtifact: (id: string) => void;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifacts,
  activeArtifactId,
  onSelectArtifact,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<"preview" | "code" | "markdown">("preview");
  const [copied, setCopied] = useState(false);

  if (!artifacts || artifacts.length === 0) return null;

  const currentArtifact =
    artifacts.find((a) => a.id === activeArtifactId) || artifacts[artifacts.length - 1];

  const handleCopy = () => {
    navigator.clipboard.writeText(currentArtifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = currentArtifact.type === "html" ? "html" : "md";
    const blob = new Blob([currentArtifact.content], {
      type: currentArtifact.type === "html" ? "text/html" : "text/markdown",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentArtifact.title.toLowerCase().replace(/\s+/g, "_")}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleOpenRaw = () => {
    const newTab = window.open();
    if (newTab) {
      newTab.document.write(currentArtifact.content);
      newTab.document.close();
    }
  };

  return (
    <div className="flex flex-col h-full bg-surface-50 border-l border-surface-200 shadow-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-3.5 border-b border-surface-200 bg-surface-100">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-semibold uppercase tracking-wider text-primary px-2 py-0.5 rounded bg-primary-muted border border-primary/20">
            Artifact
          </span>
          <h3 className="text-sm font-semibold text-zinc-100 truncate">{currentArtifact.title}</h3>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-200 transition-colors"
            title="Copy Code"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
          <button
            onClick={handleDownload}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-200 transition-colors"
            title="Download Artifact"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={handleOpenRaw}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-200 transition-colors"
            title="Open in new window"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-200 transition-colors"
            title="Close viewer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Artifact selector tabs if more than 1 */}
      {artifacts.length > 1 && (
        <div className="flex items-center gap-1 px-3 py-1.5 border-b border-surface-200 bg-surface-50 overflow-x-auto">
          {artifacts.map((art) => (
            <button
              key={art.id}
              onClick={() => onSelectArtifact(art.id)}
              className={`text-xs px-2.5 py-1 rounded-md transition-colors whitespace-nowrap ${
                art.id === currentArtifact.id
                  ? "bg-surface-200 text-white font-medium"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {art.title}
            </button>
          ))}
        </div>
      )}

      {/* View mode tabs */}
      <div className="flex items-center gap-1 px-3 py-2 border-b border-surface-200 bg-surface-100/50">
        <button
          onClick={() => setActiveTab("preview")}
          className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
            activeTab === "preview"
              ? "bg-surface-200 text-white"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Eye className="w-3.5 h-3.5" /> Preview
        </button>
        <button
          onClick={() => setActiveTab("code")}
          className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
            activeTab === "code"
              ? "bg-surface-200 text-white"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <Code2 className="w-3.5 h-3.5" /> Code
        </button>
        <button
          onClick={() => setActiveTab("markdown")}
          className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
            activeTab === "markdown"
              ? "bg-surface-200 text-white"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          <FileText className="w-3.5 h-3.5" /> Raw
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-4 overflow-y-auto">
        {activeTab === "preview" && (
          <>
            {currentArtifact.type === "html" ? (
              <SandboxedHtmlFrame
                htmlContent={currentArtifact.content}
                title={currentArtifact.title}
              />
            ) : (
              <MarkdownRenderer content={currentArtifact.content} />
            )}
          </>
        )}

        {activeTab === "code" && (
          <pre className="p-4 bg-surface-100 text-zinc-200 rounded-lg border border-surface-200 text-xs font-mono overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {currentArtifact.content}
          </pre>
        )}

        {activeTab === "markdown" && (
          <textarea
            readOnly
            value={currentArtifact.content}
            className="w-full h-full min-h-[450px] p-4 bg-surface-100 text-zinc-300 font-mono text-xs rounded-lg border border-surface-200 outline-none resize-none"
          />
        )}
      </div>
    </div>
  );
};
