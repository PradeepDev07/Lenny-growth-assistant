import React, { useState } from "react";
import { ProviderStatus } from "@/lib/types";
import {
  X,
  Copy,
  Check,
  Terminal,
  ExternalLink,
  Cpu,
  Sparkles,
  Database,
  Box,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  HelpCircle,
} from "lucide-react";

interface HelpDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  ollamaStatus?: ProviderStatus;
  onRefreshStatus?: () => void;
}

export const HelpDrawer: React.FC<HelpDrawerProps> = ({
  isOpen,
  onClose,
  ollamaStatus,
  onRefreshStatus,
}) => {
  const [activeTab, setActiveTab] = useState<"ollama" | "gemini" | "openrouter" | "transcripts" | "docker">("ollama");
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  if (!isOpen) return null;

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(id);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const isOllamaRunning = ollamaStatus?.is_running ?? false;
  const hasDefaultModel = ollamaStatus?.has_default_model ?? false;
  const installedModels = ollamaStatus?.installed_models ?? [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-xs">
      <div className="w-full max-w-lg h-full bg-surface-50 border-l border-surface-200 shadow-2xl flex flex-col p-6 animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-surface-200">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-primary" />
            <h2 className="text-base font-semibold text-zinc-100">Setup & Installation Help</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 py-3 border-b border-surface-200 overflow-x-auto text-xs scrollbar-none">
          <button
            onClick={() => setActiveTab("ollama")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
              activeTab === "ollama"
                ? "bg-primary text-white shadow-xs"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-surface-100"
            }`}
          >
            <Cpu className="w-3.5 h-3.5" /> Local Ollama
          </button>
          <button
            onClick={() => setActiveTab("gemini")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
              activeTab === "gemini"
                ? "bg-primary text-white shadow-xs"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-surface-100"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" /> Gemini Key
          </button>
          <button
            onClick={() => setActiveTab("openrouter")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
              activeTab === "openrouter"
                ? "bg-primary text-white shadow-xs"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-surface-100"
            }`}
          >
            OpenRouter
          </button>
          <button
            onClick={() => setActiveTab("transcripts")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
              activeTab === "transcripts"
                ? "bg-primary text-white shadow-xs"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-surface-100"
            }`}
          >
            <Database className="w-3.5 h-3.5" /> Ingestion
          </button>
          <button
            onClick={() => setActiveTab("docker")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
              activeTab === "docker"
                ? "bg-primary text-white shadow-xs"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-surface-100"
            }`}
          >
            <Box className="w-3.5 h-3.5" /> Docker
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto py-4 space-y-5 text-xs text-zinc-300">
          {/* TAB 1: LOCAL OLLAMA */}
          {activeTab === "ollama" && (
            <div className="space-y-4">
              {/* Live Detection Card */}
              <div className="p-3.5 rounded-xl bg-surface-100 border border-surface-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-zinc-200 flex items-center gap-1.5">
                    Live Auto-Detection Status:
                  </span>
                  {onRefreshStatus && (
                    <button
                      onClick={onRefreshStatus}
                      className="text-primary hover:text-primary-hover flex items-center gap-1 text-[11px]"
                    >
                      <RefreshCw className="w-3 h-3" /> Re-check
                    </button>
                  )}
                </div>

                {isOllamaRunning ? (
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2 text-emerald-400 font-medium">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span>Ollama Daemon is Running locally!</span>
                    </div>
                    {hasDefaultModel ? (
                      <p className="text-zinc-400 text-[11px]">
                        Default model <span className="font-mono text-zinc-200">llama3.1:8b</span> is installed and ready for offline use.
                      </p>
                    ) : (
                      <p className="text-amber-400 text-[11px] flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                        Ollama is online, but <span className="font-mono text-white">llama3.1:8b</span> is not pulled yet. See Step 3 below.
                      </p>
                    )}
                    {installedModels.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        <span className="text-[10px] text-zinc-500 uppercase tracking-wider">Installed:</span>
                        {installedModels.map((m) => (
                          <span key={m} className="px-1.5 py-0.5 rounded bg-surface-200 font-mono text-[10px] text-zinc-300">
                            {m}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-zinc-400 font-medium">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
                    <span>Ollama is currently Offline or Not Running. Follow steps below to start it:</span>
                  </div>
                )}
              </div>

              {/* Step 1: Install */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-zinc-100">Step 1: Install Ollama</span>
                  <a
                    href="https://ollama.com/download"
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary hover:text-primary-hover flex items-center gap-1 text-[11px]"
                  >
                    ollama.com <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </div>
                <p className="text-zinc-400 text-[11px]">
                  On macOS with Homebrew, run this in your terminal:
                </p>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-100 border border-surface-200 font-mono text-[11px]">
                  <code>brew install ollama</code>
                  <button
                    onClick={() => copyToClipboard("brew install ollama", "brew")}
                    className="p-1 hover:text-white text-zinc-400 transition-colors"
                  >
                    {copiedCmd === "brew" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Step 2: Start Daemon */}
              <div className="space-y-1.5">
                <span className="font-semibold text-zinc-100">Step 2: Start the Ollama Service</span>
                <p className="text-zinc-400 text-[11px]">
                  Launch the Ollama desktop app, or start the service from your terminal:
                </p>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-100 border border-surface-200 font-mono text-[11px]">
                  <code>ollama serve</code>
                  <button
                    onClick={() => copyToClipboard("ollama serve", "serve")}
                    className="p-1 hover:text-white text-zinc-400 transition-colors"
                  >
                    {copiedCmd === "serve" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Step 3: Pull Model */}
              <div className="space-y-1.5">
                <span className="font-semibold text-zinc-100">Step 3: Pull Recommended Model</span>
                <p className="text-zinc-400 text-[11px]">
                  Pull <span className="font-mono text-zinc-200">llama3.1:8b</span> (or smaller <span className="font-mono text-zinc-200">llama3.2:3b</span> for machines with 8GB RAM):
                </p>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-100 border border-surface-200 font-mono text-[11px]">
                  <code>ollama pull llama3.1:8b</code>
                  <button
                    onClick={() => copyToClipboard("ollama pull llama3.1:8b", "pull")}
                    className="p-1 hover:text-white text-zinc-400 transition-colors"
                  >
                    {copiedCmd === "pull" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Step 4: Verify */}
              <div className="space-y-1.5">
                <span className="font-semibold text-zinc-100">Step 4: Verify Reachability</span>
                <p className="text-zinc-400 text-[11px]">Check that Ollama responds on port 11434:</p>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-100 border border-surface-200 font-mono text-[11px]">
                  <code>curl http://localhost:11434/api/tags</code>
                  <button
                    onClick={() => copyToClipboard("curl http://localhost:11434/api/tags", "curl")}
                    className="p-1 hover:text-white text-zinc-400 transition-colors"
                  >
                    {copiedCmd === "curl" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: GEMINI */}
          {activeTab === "gemini" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-surface-100 border border-surface-200 space-y-2">
                <span className="font-semibold text-zinc-100 block">Why Google Gemini?</span>
                <p className="text-zinc-400 text-[11px] leading-relaxed">
                  Gemini 2.0 Flash is the primary model for Retrieval QA due to its huge context window (holding multiple transcript chunks) and sub-second token generation latency.
                </p>
                <span className="inline-block px-2 py-0.5 rounded bg-emerald-950/50 text-emerald-400 border border-emerald-800/40 text-[10px] font-semibold">
                  100% Free Tier (No credit card needed)
                </span>
              </div>

              <div className="space-y-1.5">
                <span className="font-semibold text-zinc-100">1. Get Your Free API Key</span>
                <p className="text-zinc-400 text-[11px]">Visit Google AI Studio and click "Create API key":</p>
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary/10 text-primary border border-primary/30 font-medium hover:bg-primary/20 transition-colors"
                >
                  Open Google AI Studio <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              <div className="space-y-1.5">
                <span className="font-semibold text-zinc-100">2. Add to your .env file</span>
                <p className="text-zinc-400 text-[11px]">In your project root, set the key:</p>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-100 border border-surface-200 font-mono text-[11px]">
                  <code>GEMINI_API_KEY=AIzaSy...</code>
                  <button
                    onClick={() => copyToClipboard("GEMINI_API_KEY=your_key_here", "gemini_env")}
                    className="p-1 hover:text-white text-zinc-400"
                  >
                    {copiedCmd === "gemini_env" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: OPENROUTER */}
          {activeTab === "openrouter" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-surface-100 border border-surface-200 space-y-2">
                <span className="font-semibold text-zinc-100 block">Why OpenRouter?</span>
                <p className="text-zinc-400 text-[11px] leading-relaxed">
                  OpenRouter gives unified access to top reasoning models like Claude 3.7 Sonnet and GPT-4o, used specifically by the Ship 30/30 skill for exceptional long-form narrative quality.
                </p>
              </div>

              <div className="space-y-1.5">
                <span className="font-semibold text-zinc-100">1. Generate Key</span>
                <a
                  href="https://openrouter.ai/keys"
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-purple-900/30 text-purple-400 border border-purple-800/40 font-medium hover:bg-purple-900/50 transition-colors"
                >
                  OpenRouter Keys Dashboard <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              <div className="space-y-1.5">
                <span className="font-semibold text-zinc-100">2. Add to your .env file</span>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-100 border border-surface-200 font-mono text-[11px]">
                  <code>OPENROUTER_API_KEY=sk-or-v1-...</code>
                  <button
                    onClick={() => copyToClipboard("OPENROUTER_API_KEY=your_key_here", "or_env")}
                    className="p-1 hover:text-white text-zinc-400"
                  >
                    {copiedCmd === "or_env" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: TRANSCRIPT INGESTION */}
          {activeTab === "transcripts" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-surface-100 border border-surface-200 space-y-2">
                <span className="font-semibold text-zinc-100 block">Curated Podcast Corpus</span>
                <p className="text-zinc-400 text-[11px] leading-relaxed">
                  The assistant indexes canonical episodes from Elena Verna (B2B PLG/Activation), Brian Balfour (Growth Loops), Shreyas Doshi (PM Metrics), and Lenny Rachitsky (0-to-1 PMF).
                </p>
              </div>

              <div className="space-y-1.5">
                <span className="font-semibold text-zinc-100">Re-run Ingestion & Indexing</span>
                <p className="text-zinc-400 text-[11px]">
                  To clear and re-index all podcast transcripts into the vector store:
                </p>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-100 border border-surface-200 font-mono text-[11px]">
                  <code>PYTHONPATH=. python -m ingestion.ingest --refresh</code>
                  <button
                    onClick={() => copyToClipboard("PYTHONPATH=. python -m ingestion.ingest --refresh", "ingest")}
                    className="p-1 hover:text-white text-zinc-400"
                  >
                    {copiedCmd === "ingest" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: DOCKER COMPOSE */}
          {activeTab === "docker" && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-surface-100 border border-surface-200 space-y-2">
                <span className="font-semibold text-zinc-100 block">One-Command Docker Deployment</span>
                <p className="text-zinc-400 text-[11px] leading-relaxed">
                  Spins up PostgreSQL with pgvector, FastAPI backend, Next.js frontend, and local Ollama container simultaneously.
                </p>
              </div>

              <div className="space-y-1.5">
                <span className="font-semibold text-zinc-100">Launch Everything</span>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-100 border border-surface-200 font-mono text-[11px]">
                  <code>docker compose up --build</code>
                  <button
                    onClick={() => copyToClipboard("docker compose up --build", "compose")}
                    className="p-1 hover:text-white text-zinc-400"
                  >
                    {copiedCmd === "compose" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-surface-200 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-surface-100 hover:bg-surface-200 text-xs font-medium text-zinc-300 transition-colors"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
