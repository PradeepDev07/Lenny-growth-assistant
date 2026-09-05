import React from "react";
import { ModelInfo } from "@/lib/types";
import { Cpu, AlertTriangle } from "lucide-react";

interface ProviderBadgeProps {
  modelInfo?: ModelInfo;
}

export const ProviderBadge: React.FC<ProviderBadgeProps> = ({ modelInfo }) => {
  if (!modelInfo) return null;

  const getProviderStyle = (provider: string) => {
    switch (provider.toLowerCase()) {
      case "gemini":
        return "bg-blue-900/30 text-blue-400 border-blue-800/50";
      case "openrouter":
        return "bg-purple-900/30 text-purple-400 border-purple-800/50";
      case "ollama":
        return "bg-emerald-900/30 text-emerald-400 border-emerald-800/50";
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700";
    }
  };

  const getDisplayName = (provider: string, model: string) => {
    if (provider === "gemini") {
      if (model.includes("flash-lite")) return "Gemini 2.5 Flash Lite (Free)";
      if (model.includes("2.5-flash")) return "Gemini 2.5 Flash (Free)";
      if (model.includes("2.0-flash")) return "Gemini 2.0 Flash";
      return `Gemini (${model})`;
    }
    if (provider === "openrouter") {
      if (model === "openrouter/free") return "OpenRouter (Free)";
      if (model.includes("claude")) return "Claude 3.7 (OpenRouter)";
      if (model.includes("gpt-4o")) return "GPT-4o (OpenRouter)";
      return `OpenRouter (${model.split("/").pop()})`;
    }
    if (provider === "ollama") {
      if (model.includes("3.2")) return "Ollama (Llama 3.2 3B)";
      return `Ollama (${model})`;
    }
    return `${provider} · ${model}`;
  };

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs mb-2">
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border font-medium ${getProviderStyle(
          modelInfo.provider
        )}`}
      >
        <Cpu className="w-3 h-3" />
        {getDisplayName(modelInfo.provider, modelInfo.model)}
        {modelInfo.latency_ms ? ` · ${modelInfo.latency_ms}ms` : ""}
      </span>

      {modelInfo.fallback_used && (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-950/40 text-amber-400 border border-amber-800/50">
          <AlertTriangle className="w-3 h-3" />
          ⓘ Fallback used: {modelInfo.provider}
        </span>
      )}
    </div>
  );
};
