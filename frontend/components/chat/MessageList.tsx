import React, { useEffect, useRef } from "react";
import { Message, Source, ModelInfo } from "@/lib/types";
import { ProviderBadge } from "./ProviderBadge";
import { SourceCard } from "./SourceCard";
import { PenTool, Box, User, Sparkles, Loader2 } from "lucide-react";

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  streamingSources: Source[];
  streamingModelInfo: ModelInfo | null;
  onTurnIntoShip30: (msg: Message) => void;
  onGenerateArtifact: (msg: Message) => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isStreaming,
  streamingContent,
  streamingSources,
  streamingModelInfo,
  onTurnIntoShip30,
  onGenerateArtifact,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
      {messages.length === 0 && !isStreaming && (
        <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto text-zinc-400">
          <div className="w-12 h-12 rounded-2xl bg-primary-muted border border-primary/30 flex items-center justify-center mb-4 text-primary">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold text-zinc-100 mb-2">Lenny Growth Assistant</h3>
          <p className="text-sm text-zinc-400 leading-relaxed">
            Ask deep, grounded questions about B2B PLG, activation metrics, growth loops, or product-market fit based on Lenny Rachitsky's podcast interviews.
          </p>
        </div>
      )}

      {messages.map((msg) => {
        const isUser = msg.role === "user";

        return (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-3xl ${isUser ? "ml-auto justify-end" : "mr-auto justify-start"}`}
          >
            {!isUser && (
              <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-primary flex-shrink-0 mt-1">
                <Sparkles className="w-4 h-4" />
              </div>
            )}

            <div
              className={`rounded-2xl px-4 py-3.5 max-w-2xl text-sm leading-relaxed ${
                isUser
                  ? "bg-primary text-white rounded-br-none shadow-md"
                  : "bg-surface-50 border border-surface-200 text-zinc-200 rounded-bl-none shadow-sm"
              }`}
            >
              {!isUser && msg.model_info && <ProviderBadge modelInfo={msg.model_info} />}

              <div className="whitespace-pre-wrap break-words">{msg.content}</div>

              {!isUser && msg.sources && <SourceCard sources={msg.sources} />}

              {!isUser && (
                <div className="mt-3.5 pt-2.5 border-t border-surface-200 flex flex-wrap gap-2">
                  <button
                    onClick={() => onTurnIntoShip30(msg)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-100 hover:bg-surface-200 border border-surface-200 text-xs font-medium text-zinc-300 hover:text-white transition-colors"
                  >
                    <PenTool className="w-3 h-3 text-amber-400" />
                    Turn into Ship 30/30 post
                  </button>
                  <button
                    onClick={() => onGenerateArtifact(msg)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-100 hover:bg-surface-200 border border-surface-200 text-xs font-medium text-zinc-300 hover:text-white transition-colors"
                  >
                    <Box className="w-3 h-3 text-indigo-400" />
                    Generate Interactive Artifact
                  </button>
                </div>
              )}
            </div>

            {isUser && (
              <div className="w-8 h-8 rounded-full bg-surface-200 flex items-center justify-center text-zinc-400 flex-shrink-0 mt-1">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        );
      })}

      {/* Streaming Active Bubble */}
      {isStreaming && (
        <div className="flex gap-3 max-w-3xl mr-auto justify-start">
          <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-primary flex-shrink-0 mt-1 animate-pulse">
            <Sparkles className="w-4 h-4" />
          </div>
          <div className="rounded-2xl rounded-bl-none px-4 py-3.5 max-w-2xl text-sm leading-relaxed bg-surface-50 border border-surface-200 text-zinc-200 shadow-sm">
            {streamingModelInfo && <ProviderBadge modelInfo={streamingModelInfo} />}

            <div className="whitespace-pre-wrap break-words">
              {streamingContent || (
                <span className="flex items-center gap-2 text-zinc-400">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" /> Retrieving grounded transcripts...
                </span>
              )}
            </div>

            {streamingSources.length > 0 && <SourceCard sources={streamingSources} />}
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
