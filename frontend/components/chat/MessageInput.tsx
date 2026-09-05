import React, { useState, useRef, useEffect } from "react";
import { ArrowUp, Sparkles } from "lucide-react";

interface MessageInputProps {
  onSendMessage: (content: string) => void;
  disabled: boolean;
}

const PROMPT_SUGGESTIONS = [
  "How should we define activation metrics in B2B PLG?",
  "Why do growth loops beat traditional funnels?",
  "What is the LNO framework for PM prioritization?",
  "What are the 3 canonical signs of true product-market fit?",
];

export const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-4 border-t border-surface-200 bg-background/80 backdrop-blur-sm">
      {/* Quick Prompt Chips */}
      <div className="flex gap-2 overflow-x-auto pb-3 scrollbar-none no-scrollbar">
        {PROMPT_SUGGESTIONS.map((suggestion, i) => (
          <button
            key={i}
            disabled={disabled}
            onClick={() => onSendMessage(suggestion)}
            className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full bg-surface-100 hover:bg-surface-200 border border-surface-200 text-zinc-300 hover:text-white transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-2.5 h-2.5 inline-block mr-1 text-primary" />
            {suggestion}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="relative flex items-end gap-2 bg-surface-100 rounded-2xl border border-surface-200 p-2 focus-within:border-primary/50 transition-colors">
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a growth or product question..."
          disabled={disabled}
          className="w-full bg-transparent resize-none border-none outline-none text-sm text-zinc-100 placeholder:text-zinc-500 max-h-40 px-2 py-1.5 leading-relaxed"
        />

        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="p-2 rounded-xl bg-primary text-white hover:bg-primary-hover disabled:opacity-40 disabled:hover:bg-primary transition-all flex-shrink-0"
          aria-label="Send message"
        >
          <ArrowUp className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
