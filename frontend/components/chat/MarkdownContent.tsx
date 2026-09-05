"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check } from "lucide-react";

interface MarkdownContentProps {
  content: string;
  isStreaming?: boolean;
  className?: string;
}

interface CodeBlockProps {
  language?: string;
  children: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, children }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(children);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore clipboard error
    }
  };

  return (
    <div className="my-3 rounded-lg overflow-hidden border border-surface-200 bg-surface-100/80 text-xs font-mono">
      <div className="flex items-center justify-between px-3 py-1.5 bg-surface-200/60 border-b border-surface-200/50 text-zinc-400">
        <span className="text-[11px] font-medium lowercase tracking-wider text-zinc-300">
          {language || "code"}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] hover:text-white transition-colors py-0.5 px-1.5 rounded hover:bg-surface-300/50"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="p-3 overflow-x-auto text-zinc-200 scrollbar-thin">
        <pre className="m-0 leading-relaxed font-mono">{children}</pre>
      </div>
    </div>
  );
};

export const MarkdownContent: React.FC<MarkdownContentProps> = ({
  content,
  isStreaming = false,
  className = "",
}) => {
  return (
    <div className={`markdown-body text-sm leading-relaxed ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-base sm:text-lg font-bold text-zinc-100 mt-4 mb-2 first:mt-0 tracking-tight">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-sm sm:text-base font-semibold text-zinc-100 mt-3.5 mb-1.5 pb-1 border-b border-surface-200/50 first:mt-0">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xs sm:text-sm font-semibold text-zinc-200 mt-3 mb-1 first:mt-0">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-xs font-semibold text-zinc-300 mt-2 mb-1 first:mt-0 uppercase tracking-wider">
              {children}
            </h4>
          ),
          p: ({ children }) => (
            <p className="text-sm leading-relaxed text-zinc-200 mb-2.5 last:mb-0">
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul className="list-disc list-outside pl-5 space-y-1.5 my-2 text-zinc-200 text-sm">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-outside pl-5 space-y-1.5 my-2 text-zinc-200 text-sm">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed pl-0.5 text-zinc-200">{children}</li>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-primary pl-3.5 my-2.5 py-1 bg-surface-100/40 text-zinc-300 italic rounded-r text-sm">
              {children}
            </blockquote>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-zinc-100">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-zinc-300">{children}</em>
          ),
          hr: () => <hr className="my-4 border-surface-200" />,
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline hover:text-primary-hover font-medium transition-colors"
            >
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-3 rounded-lg border border-surface-200">
              <table className="min-w-full divide-y divide-surface-200 text-xs text-left text-zinc-300">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-surface-100/80 font-semibold text-zinc-200 border-b border-surface-200">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-surface-200/50">{children}</tbody>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-surface-100/40 transition-colors">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 font-medium">{children}</th>
          ),
          td: ({ children }) => <td className="px-3 py-2">{children}</td>,
          code: ({ className, children, ...props }) => {
            const rawString = String(children).replace(/\n$/, "");
            const match = /language-(\w+)/.exec(className || "");
            const isMultiLine = rawString.includes("\n");

            // Render multi-line or tagged code block with language & copy button
            if (match || isMultiLine) {
              return (
                <CodeBlock language={match ? match[1] : undefined}>
                  {rawString}
                </CodeBlock>
              );
            }

            // Inline code chip
            return (
              <code
                className="bg-surface-200/80 text-indigo-300 px-1.5 py-0.5 rounded text-xs font-mono border border-surface-300/40"
                {...props}
              >
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>

      {isStreaming && (
        <span
          className="inline-block w-1.5 h-3.5 ml-1 bg-primary align-middle animate-pulse rounded-xs"
          aria-hidden="true"
        />
      )}
    </div>
  );
};
