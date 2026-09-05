import { useState, useCallback } from "react";
import { Message, Source, ModelInfo } from "@/lib/types";

interface UseChatStreamOptions {
  sessionId: string;
  onFinish?: (assistantMessage: Message) => void;
  onError?: (err: Error) => void;
}

export function useChatStream({ sessionId, onFinish, onError }: UseChatStreamOptions) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingSources, setStreamingSources] = useState<Source[]>([]);
  const [streamingModelInfo, setStreamingModelInfo] = useState<ModelInfo | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isStreaming) return;

      setIsStreaming(true);
      setStreamingContent("");
      setStreamingSources([]);
      setStreamingModelInfo(null);

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sessionId, content }),
        });

        if (!response.ok || !response.body) {
          throw new Error(`HTTP error ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let accumulatedText = "";
        let currentSources: Source[] = [];
        let currentModelInfo: ModelInfo | null = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let currentEvent = "message";

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const dataStr = line.slice(6).trim();
              if (!dataStr) continue;

              try {
                const parsed = JSON.parse(dataStr);
                if (currentEvent === "sources") {
                  currentSources = parsed;
                  setStreamingSources(parsed);
                } else if (currentEvent === "model_info") {
                  currentModelInfo = parsed;
                  setStreamingModelInfo(parsed);
                } else if (currentEvent === "token") {
                  if (parsed.token) {
                    accumulatedText += parsed.token;
                    setStreamingContent(accumulatedText);
                  }
                } else if (currentEvent === "done") {
                  // Finalized
                }
              } catch (err) {
                // If not JSON, raw string token fallback
                if (currentEvent === "token") {
                  accumulatedText += dataStr;
                  setStreamingContent(accumulatedText);
                }
              }
            }
          }
        }

        const finalMsg: Message = {
          id: `msg-${Date.now()}`,
          session_id: sessionId,
          role: "assistant",
          content: accumulatedText,
          sources: currentSources,
          model_info: currentModelInfo || undefined,
          created_at: new Date().toISOString(),
        };

        if (onFinish) {
          onFinish(finalMsg);
        }
      } catch (err: any) {
        if (onError) onError(err);
      } finally {
        setIsStreaming(false);
        setStreamingContent("");
        setStreamingSources([]);
        setStreamingModelInfo(null);
      }
    },
    [sessionId, isStreaming, onFinish, onError]
  );

  return {
    sendMessage,
    isStreaming,
    streamingContent,
    streamingSources,
    streamingModelInfo,
  };
}
