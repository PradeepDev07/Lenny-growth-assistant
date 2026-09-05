import React, { useState, useEffect } from "react";
import { ConfigResponse } from "@/lib/types";
import { fetchConfig, updateConfig } from "@/lib/api";
import { X, Check, Server, RefreshCw, Cpu } from "lucide-react";

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onRoutesUpdated?: () => void;
  onOpenHelp?: () => void;
}

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({
  isOpen,
  onClose,
  onRoutesUpdated,
  onOpenHelp,
}) => {

  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Editable task mapping state
  const [taskSelections, setTaskSelections] = useState<Record<string, { provider: string; model: string }>>({});

  useEffect(() => {
    if (isOpen) {
      loadConfig();
    }
  }, [isOpen]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const data = await fetchConfig();
      setConfig(data);
      const initial: Record<string, { provider: string; model: string }> = {};
      Object.entries(data.routes).forEach(([task, info]) => {
        initial[task] = { provider: info.provider, model: info.model };
      });
      setTaskSelections(initial);
    } catch (e) {
      console.error("Failed to load router config:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleTaskChange = (task: string, provider: string, model: string) => {
    setTaskSelections((prev) => ({
      ...prev,
      [task]: { provider, model },
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      for (const [task, sel] of Object.entries(taskSelections)) {
        await updateConfig(task, sel.provider, sel.model);
      }
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2000);
      if (onRoutesUpdated) onRoutesUpdated();
    } catch (e) {
      console.error("Failed to save config:", e);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-xs">
      <div className="w-full max-w-md h-full bg-surface-50 border-l border-surface-200 shadow-2xl flex flex-col p-6 animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-surface-200">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-primary" />
            <h2 className="text-base font-semibold text-zinc-100">Model Router Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto py-4 space-y-6">
          {/* Provider Health Status */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Provider Connectivity
              </h3>
              <button
                onClick={loadConfig}
                className="text-xs text-primary hover:text-primary-hover flex items-center gap-1"
              >
                <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} /> Ping
              </button>
            </div>

            {config && (
              <div className="space-y-2">
                {Object.entries(config.providers).map(([providerName, status]) => {
                  const isOllama = providerName === "ollama";
                  const isOnline = isOllama ? (status.is_running ?? status.configured) : status.configured;

                  return (
                    <div
                      key={providerName}
                      className="p-2.5 rounded-lg bg-surface-100 border border-surface-200 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 font-medium capitalize text-zinc-200">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              isOnline ? "bg-emerald-500 shadow-sm shadow-emerald-500/50" : "bg-rose-500/80"
                            }`}
                          />
                          {providerName}
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-mono text-[11px] px-2 py-0.5 rounded ${
                              isOnline
                                ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/40"
                                : "bg-zinc-800 text-zinc-400"
                            }`}
                          >
                            {isOllama
                              ? isOnline
                                ? "Running (Local)"
                                : "Offline"
                              : isOnline
                              ? "Connected"
                              : "Not Configured"}
                          </span>
                        </div>
                      </div>

                      {isOllama && !isOnline && onOpenHelp && (
                        <div className="flex items-center justify-between pt-1 text-[11px] text-zinc-400 border-t border-surface-200/50">
                          <span>Local daemon not detected.</span>
                          <button
                            onClick={() => {
                              onClose();
                              onOpenHelp();
                            }}
                            className="text-primary hover:text-primary-hover font-medium underline"
                          >
                            Ollama Setup Instructions →
                          </button>
                        </div>
                      )}

                      {isOllama && isOnline && status.installed_models && (
                        <div className="text-[10px] text-zinc-400 pt-0.5 truncate font-mono">
                          Models: {status.installed_models.join(", ") || "none pulled yet"}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

          </div>

          {/* Task Model Routing Assignments */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-3">
              Task to Model Assignment
            </h3>

            <div className="space-y-4 text-xs">
              {/* Retrieval QA */}
              <div className="p-3 rounded-lg bg-surface-100 border border-surface-200 space-y-1.5">
                <label className="font-semibold text-zinc-200 block">Retrieval QA (Grounded Chat)</label>
                <p className="text-zinc-400 text-[11px]">Answers grounded in Lenny podcast transcripts.</p>
                <select
                  value={taskSelections["retrieval_qa"]?.provider || "gemini"}
                  onChange={(e) => {
                    const prov = e.target.value;
                    const model = prov === "gemini" ? "gemini-2.0-flash" : prov === "openrouter" ? "anthropic/claude-3.5-sonnet" : "llama3.2:3b";
                    handleTaskChange("retrieval_qa", prov, model);
                  }}
                  className="w-full bg-surface-200 border border-surface-300 rounded p-1.5 text-zinc-200 outline-none focus:border-primary"
                >
                  <option value="gemini">Gemini · 2.0 Flash (Primary)</option>
                  <option value="openrouter">OpenRouter · Claude 3.5 Sonnet</option>
                  <option value="ollama">Ollama · llama3.2:3b (Local)</option>
                </select>
              </div>

              {/* Essay Generation */}
              <div className="p-3 rounded-lg bg-surface-100 border border-surface-200 space-y-1.5">
                <label className="font-semibold text-zinc-200 block">Essay Generation (Ship 30/30)</label>
                <p className="text-zinc-400 text-[11px]">Long-form structured atomic essay writing.</p>
                <select
                  value={taskSelections["essay_generation"]?.provider || "openrouter"}
                  onChange={(e) => {
                    const prov = e.target.value;
                    const model = prov === "openrouter" ? "anthropic/claude-3.7-sonnet" : prov === "gemini" ? "gemini-2.0-flash" : "llama3.2:3b";
                    handleTaskChange("essay_generation", prov, model);
                  }}
                  className="w-full bg-surface-200 border border-surface-300 rounded p-1.5 text-zinc-200 outline-none focus:border-primary"
                >
                  <option value="openrouter">OpenRouter · Claude 3.7 Sonnet (Primary)</option>
                  <option value="gemini">Gemini · 2.0 Flash</option>
                  <option value="ollama">Ollama · llama3.2:3b (Local)</option>
                </select>
              </div>

              {/* Artifact Generation */}
              <div className="p-3 rounded-lg bg-surface-100 border border-surface-200 space-y-1.5">
                <label className="font-semibold text-zinc-200 block">Artifact Generation (HTML/MD)</label>
                <p className="text-zinc-400 text-[11px]">Interactive code models and calculators.</p>
                <select
                  value={taskSelections["artifact_generation"]?.provider || "gemini"}
                  onChange={(e) => {
                    const prov = e.target.value;
                    const model = prov === "gemini" ? "gemini-2.0-flash" : prov === "openrouter" ? "openai/gpt-4o" : "llama3.2:3b";
                    handleTaskChange("artifact_generation", prov, model);
                  }}
                  className="w-full bg-surface-200 border border-surface-300 rounded p-1.5 text-zinc-200 outline-none focus:border-primary"
                >
                  <option value="gemini">Gemini · 2.0 Flash (Primary)</option>
                  <option value="openrouter">OpenRouter · GPT-4o</option>
                  <option value="ollama">Ollama · llama3.2:3b (Local)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-surface-200 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-surface-100 hover:bg-surface-200 text-xs font-medium text-zinc-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            {savedSuccess ? (
              <>
                <Check className="w-3.5 h-3.5" /> Saved!
              </>
            ) : (
              "Save Changes"
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
